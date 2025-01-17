"""Role domain service impl"""

from fss.starter.system.mapper.role_mapper import RoleMapper, roleMapper

from fss.common.service.impl.service_impl import ServiceImpl
from fss.starter.system.model.role_do import RoleDO
from fss.starter.system.service.role_service import RoleService


class RoleServiceImpl(ServiceImpl[RoleMapper, RoleDO], RoleService):
    """
    Implementation of the RoleService interface.
    """

    def __init__(self, mapper: RoleMapper):
        """
        Initialize the RoleServiceImpl instance.

        Args:
            mapper (RoleMapper): The RoleMapper instance to use for database operations.
        """
        super(RoleServiceImpl, self).__init__(mapper=mapper)
        self.mapper = mapper


def get_role_service() -> RoleService:
    """
    Return an instance of the RoleService implementation.

    Returns:
        RoleService: An instance of the RoleServiceImpl class.
    """
    return RoleServiceImpl(mapper=roleMapper)
