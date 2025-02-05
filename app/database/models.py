from datetime import datetime, timezone
import os

from sqlalchemy import DateTime, Integer, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url=os.getenv('SQLALCHEMY_URL'))

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    """
    Базовый класс для всех моделей в базе данных.
    Используется для определения таблиц и их атрибутов.
    """
    
    pass

class Vape(Base):
    """
    Модель для таблицы вейпов (vapes).
    Хранит информацию о вейпах, их бренде, линейке и наличии.
    """
    
    __tablename__ = 'vapes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id'))
    brand_line_up: Mapped[str] = mapped_column(String(30))
    availability_45_50_60: Mapped[int | None] = mapped_column(nullable=True)
    availability_20: Mapped[int | None] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column()

class Brand(Base):
    """
    Модель для таблицы брендов.
    Хранит информацию о брендах вейпов.
    """
    
    __tablename__ = 'brands'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))

class Vape_Tage(Base):
    """
    Модель для связи вейпов с тегами (many-to-many).
    Хранит информацию о вейпах и их тегах.
    """
    
    __tablename__ = 'vapes_tags'

    vape_id: Mapped[int] = mapped_column(ForeignKey('vapes.id'), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey('tags.id'), primary_key=True)

class Tag(Base):
    """
    Модель для таблицы тегов.
    Хранит информацию о тегах, которые можно присваивать вейпам.
    """
    
    __tablename__ = 'tags'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

class Vaporizer(Base):
    """
    Модель для таблицы вейперов.
    Хранит информацию о различных моделях вейперов.
    """
    
    __tablename__ = 'vaporizers'

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey('vaporizer_brands.id'))
    resistance_id: Mapped[int] = mapped_column(ForeignKey('vaporizer_resistances.id'))
    price: Mapped[float] = mapped_column()

    brand: Mapped["VaporizerBrand"] = relationship(back_populates="vaporizers")
    resistance: Mapped["VaporizerResistance"] = relationship(back_populates="vaporizers")

class VaporizerBrand(Base):
    """
    Модель для таблицы брендов вейперов.
    Хранит информацию о брендах вейперов.
    """
    
    __tablename__ = 'vaporizer_brands'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    vaporizers: Mapped[list["Vaporizer"]] = relationship(back_populates="brand", cascade="all, delete-orphan")

class VaporizerResistance(Base):
    """
    Модель для таблицы сопротивлений вейперов.
    Хранит информацию о сопротивлениях для вейперов.
    """
    
    __tablename__ = 'vaporizer_resistances'

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(String(10))

    vaporizers: Mapped[list["Vaporizer"]] = relationship(back_populates="resistance", cascade="all, delete-orphan")

class UserActionLog(Base):
    """
    Модель для таблицы логов действий пользователей.
    Хранит информацию о действиях, которые совершали пользователи.
    """
    
    __tablename__ = 'user_action_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_details: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserActionLog(id={self.id}, user_id={self.user_id}, action_type={self.action_type}, timestamp={self.timestamp})>"

class User(Base):
    """
    Модель для таблицы пользователей.
    Хранит информацию о пользователях, их активности и статистике.
    """
    
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(25))
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    command_count: Mapped[int] = mapped_column(Integer, default=0)

async def async_main():
    """
    Главная асинхронная функция для создания таблиц в базе данных.
    """
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
