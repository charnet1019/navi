"""Initial schema with all tables and default data

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime
import bcrypt

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and insert default data."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime),
    )

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('resource', sa.String(50), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.UniqueConstraint('resource', 'action', name='uq_resource_action'),
    )

    # Create user_groups table
    op.create_table(
        'user_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create navigation_groups table
    op.create_table(
        'navigation_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('icon', sa.String(50)),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create links table
    op.create_table(
        'links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('icon_path', sa.String(255)),
        sa.Column('navigation_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('navigation_groups.id'), nullable=False),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('open_in_new_tab', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('value', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('changes', postgresql.JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()'), index=True),
    )

    # Create association tables
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )

    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('granted_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    op.create_table(
        'user_group_members',
        sa.Column('user_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_groups.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('joined_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create fine-grained permission tables
    op.create_table(
        'link_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('link_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('links.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('user_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_groups.id', ondelete='CASCADE')),
        sa.Column('granted_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND user_group_id IS NULL) OR (user_id IS NULL AND user_group_id IS NOT NULL)",
            name='check_link_permission_target'
        ),
    )

    op.create_table(
        'navigation_group_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('navigation_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('navigation_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('user_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_groups.id', ondelete='CASCADE')),
        sa.Column('granted_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND user_group_id IS NULL) OR (user_id IS NULL AND user_group_id IS NOT NULL)",
            name='check_nav_group_permission_target'
        ),
    )

    # Insert default data
    conn = op.get_bind()

    # Generate UUIDs for default data
    admin_role_id = str(uuid.uuid4())
    user_role_id = str(uuid.uuid4())
    admin_user_id = str(uuid.uuid4())

    # Hash the default admin password
    hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert default roles
    conn.execute(
        sa.text("""
            INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
            VALUES
                (:admin_role_id, 'Admin', 'Full system access', true, now(), now()),
                (:user_role_id, 'User', 'Standard user access', true, now(), now())
        """),
        {
            'admin_role_id': admin_role_id,
            'user_role_id': user_role_id
        }
    )

    # Insert default permissions
    permissions = [
        # User management
        ('users:read', 'users', 'read', 'View users'),
        ('users:create', 'users', 'create', 'Create users'),
        ('users:update', 'users', 'update', 'Update users'),
        ('users:delete', 'users', 'delete', 'Delete users'),
        # Role management
        ('roles:read', 'roles', 'read', 'View roles'),
        ('roles:create', 'roles', 'create', 'Create roles'),
        ('roles:update', 'roles', 'update', 'Update roles'),
        ('roles:delete', 'roles', 'delete', 'Delete roles'),
        # Permission management
        ('permissions:read', 'permissions', 'read', 'View permissions'),
        ('permissions:assign', 'permissions', 'assign', 'Assign permissions'),
        # Navigation group management
        ('navigation_groups:read', 'navigation_groups', 'read', 'View navigation groups'),
        ('navigation_groups:create', 'navigation_groups', 'create', 'Create navigation groups'),
        ('navigation_groups:update', 'navigation_groups', 'update', 'Update navigation groups'),
        ('navigation_groups:delete', 'navigation_groups', 'delete', 'Delete navigation groups'),
        # Link management
        ('links:read', 'links', 'read', 'View links'),
        ('links:create', 'links', 'create', 'Create links'),
        ('links:update', 'links', 'update', 'Update links'),
        ('links:delete', 'links', 'delete', 'Delete links'),
        # System settings
        ('system_settings:read', 'system_settings', 'read', 'View system settings'),
        ('system_settings:update', 'system_settings', 'update', 'Update system settings'),
        # Audit logs
        ('audit_logs:read', 'audit_logs', 'read', 'View audit logs'),
        # User groups
        ('user_groups:read', 'user_groups', 'read', 'View user groups'),
        ('user_groups:create', 'user_groups', 'create', 'Create user groups'),
        ('user_groups:update', 'user_groups', 'update', 'Update user groups'),
        ('user_groups:delete', 'user_groups', 'delete', 'Delete user groups'),
    ]

    permission_ids = {}
    for name, resource, action, description in permissions:
        perm_id = str(uuid.uuid4())
        permission_ids[name] = perm_id
        conn.execute(
            sa.text("""
                INSERT INTO permissions (id, name, resource, action, description)
                VALUES (:id, :name, :resource, :action, :description)
            """),
            {
                'id': perm_id,
                'name': name,
                'resource': resource,
                'action': action,
                'description': description
            }
        )

    # Assign all permissions to Admin role
    for perm_id in permission_ids.values():
        conn.execute(
            sa.text("""
                INSERT INTO role_permissions (role_id, permission_id, granted_at)
                VALUES (:role_id, :permission_id, now())
            """),
            {
                'role_id': admin_role_id,
                'permission_id': perm_id
            }
        )

    # Assign read-only permissions to User role
    user_permissions = [
        'navigation_groups:read',
        'links:read',
    ]
    for perm_name in user_permissions:
        if perm_name in permission_ids:
            conn.execute(
                sa.text("""
                    INSERT INTO role_permissions (role_id, permission_id, granted_at)
                    VALUES (:role_id, :permission_id, now())
                """),
                {
                    'role_id': user_role_id,
                    'permission_id': permission_ids[perm_name]
                }
            )

    # Insert default admin user
    conn.execute(
        sa.text("""
            INSERT INTO users (id, username, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
            VALUES (:id, 'admin', 'admin@navi.local', :hashed_password, 'System Administrator', true, true, now(), now())
        """),
        {
            'id': admin_user_id,
            'hashed_password': hashed_password
        }
    )

    # Assign Admin role to admin user
    conn.execute(
        sa.text("""
            INSERT INTO user_roles (user_id, role_id, assigned_at)
            VALUES (:user_id, :role_id, now())
        """),
        {
            'user_id': admin_user_id,
            'role_id': admin_role_id
        }
    )

    # Insert default system setting
    conn.execute(
        sa.text("""
            INSERT INTO system_settings (id, key, value, description, updated_at)
            VALUES (:id, 'links_per_row', '5', 'Number of links to display per row', now())
        """),
        {
            'id': str(uuid.uuid4())
        }
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('navigation_group_permissions')
    op.drop_table('link_permissions')
    op.drop_table('user_group_members')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('audit_logs')
    op.drop_table('system_settings')
    op.drop_table('links')
    op.drop_table('navigation_groups')
    op.drop_table('user_groups')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
