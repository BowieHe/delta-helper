"""
数据库管理模块

使用SQLite存储游戏会话和物资记录
支持历史查询、统计分析和CSV导出
"""

import sqlite3
import csv
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from loguru import logger


class DatabaseManager:
    """游戏数据分析数据库管理器"""

    def __init__(self, db_path: str = "data/sessions.db"):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"DatabaseManager initialized: {self.db_path}")

    @contextmanager
    def _get_conn(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_conn() as conn:
            # 游戏会话表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    map_name TEXT DEFAULT 'unknown',
                    result TEXT CHECK(result IN ('success', 'death', 'disconnect')),
                    total_value INTEGER DEFAULT 0,
                    duration_seconds INTEGER DEFAULT 0,
                    value_per_minute REAL DEFAULT 0.0,
                    materials_count INTEGER DEFAULT 0
                )
            """)

            # 物资明细表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS loot_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    name TEXT NOT NULL,
                    category TEXT CHECK(category IN ('weapon', 'medical', 'equipment', 'valuables', 'ammo', 'unknown')),
                    value INTEGER DEFAULT 0,
                    position_x INTEGER,
                    position_y INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL DEFAULT 0.0,
                    FOREIGN KEY (session_id) REFERENCES game_sessions(id) ON DELETE CASCADE
                )
            """)

            # 创建索引优化查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_time 
                ON game_sessions(start_time)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_loot_session 
                ON loot_items(session_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_loot_category 
                ON loot_items(category)
            """)

            logger.info("Database tables initialized")

    def create_session(self, map_name: str = "unknown") -> int:
        """
        创建新游戏会话

        Args:
            map_name: 地图名称

        Returns:
            会话ID
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO game_sessions (map_name, start_time) VALUES (?, ?)",
                (map_name, datetime.now()),
            )
            session_id = cursor.lastrowid
            logger.info(f"Created game session: {session_id}")
            return session_id

    def end_session(
        self,
        session_id: int,
        result: str,
        total_value: int = 0,
        materials_count: int = 0,
    ):
        """
        结束游戏会话

        Args:
            session_id: 会话ID
            result: 结果 ('success', 'death', 'disconnect')
            total_value: 总价值
            materials_count: 物资数量
        """
        end_time = datetime.now()

        with self._get_conn() as conn:
            # 获取开始时间
            row = conn.execute(
                "SELECT start_time FROM game_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            if not row:
                logger.error(f"Session {session_id} not found")
                return

            start_time = datetime.fromisoformat(row["start_time"])
            duration = (end_time - start_time).total_seconds()
            value_per_minute = (total_value / (duration / 60)) if duration > 0 else 0

            # 更新会话记录
            conn.execute(
                """
                UPDATE game_sessions 
                SET end_time = ?, result = ?, total_value = ?, 
                    duration_seconds = ?, value_per_minute = ?, materials_count = ?
                WHERE id = ?
            """,
                (
                    end_time,
                    result,
                    total_value,
                    int(duration),
                    value_per_minute,
                    materials_count,
                    session_id,
                ),
            )

            logger.info(
                f"Ended session {session_id}: {materials_count} items, "
                f"{total_value} value, {duration:.1f}s"
            )

    def add_loot_item(
        self,
        session_id: int,
        name: str,
        category: str,
        value: int,
        position_x: int,
        position_y: int,
        confidence: float = 0.0,
    ):
        """
        添加物资记录

        Args:
            session_id: 会话ID
            name: 物资名称
            category: 分类 ('weapon', 'medical', 'equipment', 'valuables', 'ammo', 'unknown')
            value: 价值
            position_x: X坐标
            position_y: Y坐标
            confidence: 识别置信度
        """
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO loot_items 
                (session_id, name, category, value, position_x, position_y, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (session_id, name, category, value, position_x, position_y, confidence),
            )

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的游戏会话

        Args:
            limit: 返回数量

        Returns:
            会话列表
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM game_sessions 
                ORDER BY start_time DESC 
                LIMIT ?
            """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        """
        获取会话详情（包括物资明细）

        Args:
            session_id: 会话ID

        Returns:
            会话详情
        """
        with self._get_conn() as conn:
            session = conn.execute(
                "SELECT * FROM game_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            if not session:
                return {}

            loot_items = conn.execute(
                "SELECT * FROM loot_items WHERE session_id = ?", (session_id,)
            ).fetchall()

            result = dict(session)
            result["loot_items"] = [dict(item) for item in loot_items]
            return result

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取每日统计

        Args:
            days: 天数

        Returns:
            每日统计列表
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT 
                    date(start_time) as date,
                    COUNT(*) as sessions_count,
                    SUM(total_value) as total_value,
                    AVG(total_value) as avg_value,
                    SUM(materials_count) as total_materials,
                    AVG(value_per_minute) as avg_efficiency
                FROM game_sessions
                WHERE start_time >= datetime('now', ?)
                GROUP BY date(start_time)
                ORDER BY date
            """,
                (f"-{days} days",),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_overall_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取总体统计

        Args:
            days: 统计天数

        Returns:
            总体统计
        """
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_games,
                    SUM(total_value) as total_value,
                    AVG(total_value) as avg_value,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    AVG(value_per_minute) as avg_efficiency
                FROM game_sessions
                WHERE start_time >= datetime('now', ?)
            """,
                (f"-{days} days",),
            ).fetchone()

            return (
                dict(row)
                if row
                else {
                    "total_games": 0,
                    "total_value": 0,
                    "avg_value": 0,
                    "avg_duration": 0,
                    "success_rate": 0,
                    "avg_efficiency": 0,
                }
            )

    def get_top_items(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取最常获得的物资排行

        Args:
            limit: 返回数量
            days: 统计天数

        Returns:
            物资排行
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT 
                    name,
                    category,
                    COUNT(*) as times_found,
                    SUM(value) as total_value
                FROM loot_items
                WHERE timestamp >= datetime('now', ?)
                GROUP BY name
                ORDER BY times_found DESC
                LIMIT ?
            """,
                (f"-{days} days", limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def export_to_csv(self, filename: str, days: int = 30) -> bool:
        """
        导出数据到CSV

        Args:
            filename: 文件名
            days: 导出天数

        Returns:
            是否成功
        """
        try:
            sessions = self.get_recent_sessions(limit=1000)

            if not sessions:
                logger.warning("No sessions to export")
                return False

            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # 表头
                writer.writerow(
                    [
                        "会话ID",
                        "开始时间",
                        "结束时间",
                        "地图",
                        "结果",
                        "总价值",
                        "物资数",
                        "时长(秒)",
                        "效率(价值/分钟)",
                    ]
                )

                # 数据
                for session in sessions:
                    writer.writerow(
                        [
                            session["id"],
                            session["start_time"],
                            session["end_time"],
                            session["map_name"],
                            session["result"],
                            session["total_value"],
                            session["materials_count"],
                            session["duration_seconds"],
                            f"{session['value_per_minute']:.2f}",
                        ]
                    )

            logger.info(f"Exported {len(sessions)} sessions to {filename}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def delete_old_sessions(self, days: int = 90):
        """
        删除旧会话（清理数据）

        Args:
            days: 保留天数
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM game_sessions WHERE start_time < datetime('now', ?)",
                (f"-{days} days",),
            )
            logger.info(f"Deleted {cursor.rowcount} old sessions")


# 便捷函数：获取默认数据库实例
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """获取全局数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
