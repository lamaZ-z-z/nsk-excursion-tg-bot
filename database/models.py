'''Module with models used in database'''
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func, Boolean
from common import default_image, MAINB_DESCRIPTION


class Base(DeclarativeBase):
    '''
    Базовый наследуемый класс
    '''
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class MainBanner(Base):
    '''
    Таблица для главной страницы бота 
    (начальная страница) после нажатия /start
     '''

    __tablename__ = 'main_banner'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)

    image: Mapped[str] = mapped_column(String(150), default=default_image)

    description: Mapped[str] = mapped_column(Text, default=MAINB_DESCRIPTION)



class District(Base):
    '''
    Таблица для 
    '''
    __tablename__ = 'district'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)

    image: Mapped[str] = mapped_column(String(150), default=default_image)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    translit_name: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[str] = mapped_column(Text, default='Описания для этого района пока нет')



class Place(Base):
    '''
    Таблица для экскурсионных мест
    '''
    __tablename__ = 'place'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)

    district_name: Mapped[str] = mapped_column(ForeignKey('district.name', ondelete="CASCADE"), nullable=False)
    district_translit_name: Mapped[str] = mapped_column(ForeignKey('district.translit_name', ondelete="CASCADE"), nullable=False)


    name: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    image: Mapped[str] = mapped_column(String(150), default=default_image)

    TwoGisURL: Mapped[str] = mapped_column(Text, nullable=False)


class PlaceSuggestion(Base):
    '''
    Класс для мест из предложки
    '''
    __tablename__ = 'place_suggestion'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    # Район
    district_id: Mapped[int] = mapped_column(
        ForeignKey('district.id', ondelete="CASCADE"), nullable=False)
    district_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Название места
    place_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Фото места
    has_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_url: Mapped[str] = mapped_column(String(150), default='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSbKNeVHxSwGdiF7nCCIKZeGgDKh7aS3h9jDw&s')
    # Описание
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Местоположение (2GIS)
    location_url: Mapped[str] = mapped_column(Text, nullable=True)
    # Кто предложил
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # Telegram user ID
    username: Mapped[str] = mapped_column(String(100), nullable=True)  # Telegram username
    full_name: Mapped[str] = mapped_column(String(200), nullable=True)  # Полное имя пользователя
    # Статус предложки
    status: Mapped[str] = mapped_column(
        String(20), default='pending')  # pending, approved, rejected
        
