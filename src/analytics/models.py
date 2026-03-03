from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class LootItemRecord:
    id: Optional[int]
    session_id: int
    name: str
    category: str  # 'weapon', 'medical', 'equipment', 'valuables', 'ammo', 'unknown'
    value: int
    position_x: int
    position_y: int
    timestamp: datetime
    confidence: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LootItemRecord":
        ts = d.get("timestamp")
        if isinstance(ts, datetime):
            timestamp = ts
        else:
            timestamp = datetime.fromisoformat(ts) if ts is not None else datetime.now()
        return cls(
            id=d.get("id"),
            session_id=d["session_id"],
            name=d["name"],
            category=d.get("category", "unknown"),
            value=d.get("value", 0),
            position_x=d.get("position_x", 0),
            position_y=d.get("position_y", 0),
            timestamp=timestamp,
            confidence=d.get("confidence", 0.0),
        )

    def formatted_position(self) -> str:
        return f"({self.position_x}, {self.position_y})"


@dataclass
class GameSession:
    id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    map_name: str
    result: Optional[str]  # 'success', 'death', 'disconnect'
    total_value: int
    duration_seconds: int
    value_per_minute: float
    materials_count: int
    loot_items: List[LootItemRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "map_name": self.map_name,
            "result": self.result,
            "total_value": self.total_value,
            "duration_seconds": self.duration_seconds,
            "value_per_minute": self.value_per_minute,
            "materials_count": self.materials_count,
            "loot_items": [li.to_dict() for li in self.loot_items],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameSession":
        loot: List[LootItemRecord] = []
        if isinstance(d.get("loot_items"), list):
            loot = [LootItemRecord.from_dict(ld) for ld in d["loot_items"]]
        start_time = datetime.fromisoformat(d["start_time"])
        end_time_val = d.get("end_time")
        end_time = datetime.fromisoformat(end_time_val) if end_time_val else None
        return cls(
            id=d.get("id"),
            start_time=start_time,
            end_time=end_time,
            map_name=d.get("map_name", ""),
            result=d.get("result"),
            total_value=d.get("total_value", 0),
            duration_seconds=d.get("duration_seconds", 0),
            value_per_minute=d.get("value_per_minute", 0.0),
            materials_count=d.get("materials_count", 0),
            loot_items=loot,
        )

    def formatted_duration(self) -> str:
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def formatted_value(self) -> str:
        return f"{self.total_value:,}"


@dataclass
class DailyStats:
    date: str  # "YYYY-MM-DD"
    sessions_count: int
    total_value: int
    avg_value: float
    total_materials: int
    avg_efficiency: float

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "sessions_count": self.sessions_count,
            "total_value": self.total_value,
            "avg_value": self.avg_value,
            "total_materials": self.total_materials,
            "avg_efficiency": self.avg_efficiency,
        }

    def formatted_date(self) -> str:
        try:
            dt = datetime.fromisoformat(self.date)
            return f"{dt.month}月{dt.day}日"
        except Exception:
            return self.date


@dataclass
class OverallStats:
    total_games: int
    total_value: int
    avg_value: float
    avg_duration: float  # in seconds
    success_rate: float  # percentage 0-100
    avg_efficiency: float
    best_session_value: int
    favorite_item: str

    def to_dict(self) -> dict:
        return {
            "total_games": self.total_games,
            "total_value": self.total_value,
            "avg_value": self.avg_value,
            "avg_duration": self.avg_duration,
            "success_rate": self.success_rate,
            "avg_efficiency": self.avg_efficiency,
            "best_session_value": self.best_session_value,
            "favorite_item": self.favorite_item,
        }

    def formatted_success_rate(self) -> str:
        return f"{self.success_rate:.1f}%"

    def formatted_avg_duration(self) -> str:
        minutes = int(self.avg_duration) // 60
        seconds = int(self.avg_duration) % 60
        return f"{minutes}分{seconds:02d}秒"
