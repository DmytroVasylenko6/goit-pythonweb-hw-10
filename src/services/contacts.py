from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.contacts import ContactRepository
from src.schemas import ContactModel


class ContactService:
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        if await self.repository.is_contact_exists(body.email, body.phone, user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contact with '{body.email}' email or '{body.phone}' phone number already exists.",
            )
        return await self.repository.create_contact(body, user)

    async def get_contacts(
        self, name: str, surname: str, email: str, skip: int, limit: int, user: User
    ):
        return await self.repository.get_contacts(
            name, surname, email, skip, limit, user
        )

    async def get_contact(self, contact_id: int, user: User):
        contact = await self.repository.get_contact_by_id(contact_id, user)
        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        return contact

    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        updated_contact = await self.repository.update_contact(contact_id, body, user)
        if updated_contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        return updated_contact

    async def remove_contact(self, contact_id: int, user: User):
        deleted_contact = await self.repository.remove_contact(contact_id, user)
        if deleted_contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )
        return deleted_contact

    async def get_upcoming_birthdays(self, days: int, user: User):
        return await self.repository.get_upcoming_birthdays(days, user)
