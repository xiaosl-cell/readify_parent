"""
Example service - you can delete this file and create your own services
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.example import ExampleRepository
from app.schemas.example import ExampleCreate, ExampleUpdate, ExampleResponse, ExampleListResponse


class ExampleService:
    """
    Business logic for Example operations
    """
    
    def __init__(self, db: Session):
        self.repository = ExampleRepository(db)
    
    def create_example(self, example_in: ExampleCreate) -> ExampleResponse:
        """
        Create a new example
        
        Args:
            example_in: Example creation data
            
        Returns:
            Created example
        """
        example_dict = example_in.model_dump()
        example = self.repository.create(example_dict)
        return ExampleResponse.model_validate(example)
    
    def get_example(self, example_id: str) -> Optional[ExampleResponse]:
        """
        Get example by ID
        
        Args:
            example_id: Example ID
            
        Returns:
            Example or None
        """
        example = self.repository.get(example_id)
        if example:
            return ExampleResponse.model_validate(example)
        return None
    
    def get_examples(self, skip: int = 0, limit: int = 100) -> ExampleListResponse:
        """
        Get all examples with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of examples with total count
        """
        examples = self.repository.get_all(skip=skip, limit=limit)
        total = self.repository.count()
        
        return ExampleListResponse(
            total=total,
            items=[ExampleResponse.model_validate(ex) for ex in examples]
        )
    
    def get_active_examples(self, skip: int = 0, limit: int = 100) -> ExampleListResponse:
        """
        Get all active examples
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active examples
        """
        examples = self.repository.get_active(skip=skip, limit=limit)
        total = len(examples)
        
        return ExampleListResponse(
            total=total,
            items=[ExampleResponse.model_validate(ex) for ex in examples]
        )
    
    def update_example(self, example_id: str, example_in: ExampleUpdate) -> Optional[ExampleResponse]:
        """
        Update an example
        
        Args:
            example_id: Example ID
            example_in: Updated example data
            
        Returns:
            Updated example or None
        """
        example_dict = example_in.model_dump(exclude_unset=True)
        example = self.repository.update(example_id, example_dict)
        if example:
            return ExampleResponse.model_validate(example)
        return None
    
    def delete_example(self, example_id: str) -> bool:
        """
        Delete an example
        
        Args:
            example_id: Example ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(example_id)

