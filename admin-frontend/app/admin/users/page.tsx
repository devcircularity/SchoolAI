// app/admin/users/page.tsx - User Management with dynamic header
"use client";
import { useState, useEffect } from "react";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { userService, User, UserStats } from "@/services/user";
import { useAuth } from "@/contexts/AuthContext";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import Button from "@/components/ui/Button";
import { Edit, Trash2, UserPlus, ToggleLeft, ToggleRight, Shield } from "lucide-react";

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    total: 0,
    hasNext: false
  });
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showCreateUser, setShowCreateUser] = useState(false);

  // Set page title in header
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'User Management',
      subtitle: 'Manage users and their permissions' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  useEffect(() => {
    loadUsers();
  }, [selectedRole]);

  const loadUsers = async (page = 1) => {
    try {
      setLoading(true);
      const response = await userService.getUsers({
        page,
        limit: 20,
        role: selectedRole || undefined
      });
      
      setUsers(response.users);
      setPagination({
        currentPage: response.page,
        totalPages: Math.ceil(response.total / 20),
        total: response.total,
        hasNext: response.has_next
      });
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (user: User) => {
    if (user.id === currentUser?.user_id) {
      alert("You cannot deactivate your own account");
      return;
    }

    try {
      await userService.toggleUserStatus(user.id);
      loadUsers(pagination.currentPage);
    } catch (error) {
      console.error('Failed to toggle user status:', error);
    }
  };

  const handleDeactivateUser = async (user: User) => {
    if (user.id === currentUser?.user_id) {
      alert("You cannot deactivate your own account");
      return;
    }

    if (confirm(`Are you sure you want to deactivate ${user.full_name}? This action requires super admin privileges.`)) {
      try {
        await userService.deactivateUser(user.id);
        loadUsers(pagination.currentPage);
      } catch (error) {
        console.error('Failed to deactivate user:', error);
        alert('Failed to deactivate user. You may need super admin privileges for this action.');
      }
    }
  };

  const handleEditRoles = (user: User) => {
    setEditingUser(user);
  };

  const handleSaveRoles = async (userId: string, roles: string[]) => {
    try {
      await userService.updateUserRoles(userId, { roles });
      setEditingUser(null);
      loadUsers(pagination.currentPage);
    } catch (error) {
      console.error('Failed to update user roles:', error);
      alert('Failed to update user roles. Check your permissions.');
    }
  };

  const columns: TableColumn<User>[] = [
    {
      key: 'full_name',
      label: 'User',
      sortable: true,
      render: (name: string, user: User) => (
        <div className="min-w-0">
          <div className="font-medium text-sm truncate">{name}</div>
          <div className="text-xs text-neutral-500 truncate">{user.email}</div>
        </div>
      ),
      width: '200px',
    },
    {
      key: 'roles',
      label: 'Roles',
      render: (roles: string[]) => (
        <div className="flex flex-wrap gap-1 min-w-0">
          {roles.slice(0, 2).map(role => (
            <span
              key={role}
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                role === 'SUPER_ADMIN' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200' :
                role === 'ADMIN' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200' :
                role === 'TEACHER' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
                role === 'TESTER' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200' :
                'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200'
              }`}
            >
              {role}
            </span>
          ))}
          {roles.length > 2 && (
            <span className="text-xs text-neutral-500">+{roles.length - 2}</span>
          )}
        </div>
      ),
      width: '150px',
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (isActive: boolean, user: User) => (
        <div className="space-y-1">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
              isActive
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}
          >
            {isActive ? 'Active' : 'Inactive'}
          </span>
          {!user.is_verified && (
            <div>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800 whitespace-nowrap">
                Unverified
              </span>
            </div>
          )}
        </div>
      ),
      width: '100px',
    },
    {
      key: 'school_count',
      label: 'Schools',
      render: (count: number) => (
        <span className="text-sm">{count.toString()}</span>
      ),
      width: '80px',
    },
    {
      key: 'last_login',
      label: 'Last Login',
      render: (lastLogin: string) => (
        <span className="text-sm whitespace-nowrap">
          {lastLogin ? new Date(lastLogin).toLocaleDateString() : 'Never'}
        </span>
      ),
      width: '120px',
    },
  ];

  const actions: TableAction<User>[] = [
    {
      label: 'Roles',
      icon: <Shield size={14} />,
      onClick: handleEditRoles,
      variant: 'secondary',
    },
    {
      label: 'Toggle',
      icon: <ToggleLeft size={14} />,
      onClick: handleToggleStatus,
      variant: 'secondary',
      disabled: (user) => user.id === currentUser?.user_id,
    },
    {
      label: 'Delete',
      icon: <Trash2 size={14} />,
      onClick: handleDeactivateUser,
      variant: 'danger',
      disabled: (user) => user.id === currentUser?.user_id || !user.is_active,
    },
  ];

  // Check permissions
  const hasManageUsersPermission = currentUser?.permissions?.can_manage_users || 
                                   currentUser?.permissions?.is_admin || 
                                   currentUser?.permissions?.is_super_admin;

  if (!hasManageUsersPermission) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to manage users.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Fixed Header */}
      <div className="flex-none p-6 border-b border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
        {/* Add User Button and Total Count - Right aligned since title is in HeaderBar */}
        <div className="flex justify-between items-center mb-6">
          <p className="text-sm text-neutral-600">
            {pagination.total} total users
          </p>
          <Button 
            onClick={() => setShowCreateUser(true)}
            className="flex items-center gap-2 text-sm whitespace-nowrap"
          >
            <UserPlus size={16} />
            Add User
          </Button>
        </div>

        {/* Role Filter */}
        <div className="card p-4">
          <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
            <label className="text-sm font-medium whitespace-nowrap">Filter by Role:</label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="input w-full sm:w-48 text-sm"
            >
              <option value="">All Roles</option>
              <option value="SUPER_ADMIN">Super Admin</option>
              <option value="ADMIN">Admin</option>
              <option value="TEACHER">Teacher</option>
              <option value="ACCOUNTANT">Accountant</option>
              <option value="TESTER">Tester</option>
              <option value="PARENT">Parent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Scrollable Table Area */}
      <div className="flex-1 min-h-0 p-6">
        <div className="h-full">
          <DataTable
            data={users}
            columns={columns}
            actions={actions}
            loading={loading}
            searchable
            searchPlaceholder="Search users..."
            pagination={{
              currentPage: pagination.currentPage,
              totalPages: pagination.totalPages,
              onPageChange: loadUsers,
            }}
            emptyMessage="No users found"
            className="h-full"
          />
        </div>
      </div>

      {/* Edit Roles Modal */}
      {editingUser && (
        <EditRolesModal
          user={editingUser}
          onSave={handleSaveRoles}
          onClose={() => setEditingUser(null)}
        />
      )}

      {/* Create User Modal */}
      {showCreateUser && (
        <CreateUserModal
          onSave={(userData) => {
            userService.createUser(userData).then(() => {
              loadUsers();
              setShowCreateUser(false);
            }).catch(error => {
              console.error('Failed to create user:', error);
              alert('Failed to create user');
            });
          }}
          onClose={() => setShowCreateUser(false)}
        />
      )}
    </div>
  );
}

// Edit Roles Modal Component
function EditRolesModal({ 
  user, 
  onSave, 
  onClose 
}: { 
  user: User; 
  onSave: (userId: string, roles: string[]) => void; 
  onClose: () => void; 
}) {
  const [selectedRoles, setSelectedRoles] = useState<string[]>(user.roles);
  
  const availableRoles = [
    'SUPER_ADMIN', 'ADMIN', 'TEACHER', 'ACCOUNTANT', 'TESTER', 'PARENT'
  ];

  const toggleRole = (role: string) => {
    setSelectedRoles(prev => 
      prev.includes(role) 
        ? prev.filter(r => r !== role)
        : [...prev, role]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">
            Edit Roles for {user.full_name}
          </h2>
          
          <div className="space-y-3">
            {availableRoles.map(role => (
              <label key={role} className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedRoles.includes(role)}
                  onChange={() => toggleRole(role)}
                  className="rounded"
                />
                <span className="text-sm">{role.replace('_', ' ')}</span>
              </label>
            ))}
          </div>
          
          <div className="flex gap-3 mt-6">
            <Button 
              onClick={() => onSave(user.id, selectedRoles)}
              className="flex-1 text-sm"
            >
              Save Changes
            </Button>
            <Button 
              onClick={onClose}
              className="btn-secondary flex-1 text-sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Create User Modal Component
function CreateUserModal({ 
  onSave, 
  onClose 
}: { 
  onSave: (userData: any) => void; 
  onClose: () => void; 
}) {
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    roles: ['PARENT'],
    is_active: true
  });

  const availableRoles = [
    'SUPER_ADMIN', 'ADMIN', 'TEACHER', 'ACCOUNTANT', 'TESTER', 'PARENT'
  ];

  const toggleRole = (role: string) => {
    setFormData(prev => ({
      ...prev,
      roles: prev.roles.includes(role) 
        ? prev.roles.filter(r => r !== role)
        : [...prev.roles, role]
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Create New User</h2>
          
          <div className="space-y-4">
            <div>
              <label className="label text-sm">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                className="input text-sm"
                required
              />
            </div>
            
            <div>
              <label className="label text-sm">Full Name</label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                className="input text-sm"
                required
              />
            </div>
            
            <div>
              <label className="label text-sm">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                className="input text-sm"
                required
              />
            </div>
            
            <div>
              <label className="label text-sm">Roles</label>
              <div className="space-y-2 mt-2">
                {availableRoles.map(role => (
                  <label key={role} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={formData.roles.includes(role)}
                      onChange={() => toggleRole(role)}
                      className="rounded"
                    />
                    <span className="text-sm">{role.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Active User</span>
              </label>
            </div>
          </div>
          
          <div className="flex gap-3 mt-6">
            <Button 
              onClick={() => onSave(formData)}
              className="flex-1 text-sm"
              disabled={!formData.email || !formData.full_name || !formData.password}
            >
              Create User
            </Button>
            <Button 
              onClick={onClose}
              className="btn-secondary flex-1 text-sm"
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}