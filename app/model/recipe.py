from datetime import timedelta

from sqlalchemy import Index, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RecipeRate(Base):
    __tablename__ = 'recipe_rate'
    __table_args__ = (
        Index(
            'ix_user_rating_composite_pk',
            'user_id',
            'recipe_id',
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True,
    )
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey('recipe.id', ondelete='CASCADE'),
        primary_key=True,
    )
    rate: Mapped[int] = mapped_column(nullable=False)


class Recipe(Base):
    __tablename__ = 'recipe'

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(127), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='RESTRICT'),
        nullable=False,
    )
    ingredients: Mapped[list['RecipeIngredientAssociation']] = relationship(
        cascade='all, delete-orphan',
    )
    steps: Mapped[list['Step']] = relationship(
        back_populates='recipe',
        cascade='all, delete-orphan',
    )
    rates: Mapped[list['RecipeRate']] = relationship(
        cascade='all, delete-orphan',
    )


class RecipeIngredientAssociation(Base):
    __tablename__ = 'recipe_ingredient_association'
    __table_args__ = (
        Index(
            'ix_recipe_ingredient_association_composite_pk',
            'recipe_id',
            'ingredient_id',
        ),
    )

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey('recipe.id', ondelete='CASCADE'),
        primary_key=True,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey('ingredient.id', ondelete='RESTRICT'),
        primary_key=True,
    )
    ingredient: Mapped['Ingredient'] = relationship()


class Ingredient(Base):
    __tablename__ = 'ingredient'

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(127),
        nullable=False,
        unique=True,
    )


class Step(Base):
    __tablename__ = 'step'
    __table_args__ = (Index('ix_step_composite_pk', 'recipe_id', 'order'),)

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey('recipe.id', ondelete='CASCADE'),
        primary_key=True,
    )
    recipe: Mapped['Recipe'] = relationship(back_populates='steps')
    order: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[timedelta] = mapped_column(nullable=False)
    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='RESTRICT'),
        nullable=False,
    )
