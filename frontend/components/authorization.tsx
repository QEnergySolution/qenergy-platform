"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Plus, Trash2, Shield, Users } from "lucide-react"
import { useLanguage } from "@/hooks/use-language"

interface Permission {
  id: string
  name: string
  description: string
}

interface User {
  id: string
  name: string
  email: string
  permissions: string[]
}

export function Authorization() {
  const { t } = useLanguage()
  const [permissions, setPermissions] = useState<Permission[]>([
    { id: "ADMIN", name: "Administrator", description: "Full system access" },
    { id: "PROJECT_VIEW", name: "Project Viewer", description: "View project information" },
    { id: "PROJECT_EDIT", name: "Project Editor", description: "Edit project information" },
    { id: "REPORT_VIEW", name: "Report Viewer", description: "View reports" },
    { id: "REPORT_EDIT", name: "Report Editor", description: "Edit and upload reports" },
  ])

  const [users, setUsers] = useState<User[]>([
    { id: "1", name: "John Smith", email: "john.smith@company.com", permissions: ["ADMIN", "PROJECT_VIEW"] },
    {
      id: "2",
      name: "Sarah Johnson",
      email: "sarah.johnson@company.com",
      permissions: ["PROJECT_VIEW", "REPORT_VIEW"],
    },
    { id: "3", name: "Mike Chen", email: "mike.chen@company.com", permissions: ["REPORT_EDIT", "PROJECT_EDIT"] },
  ])

  const [newPermission, setNewPermission] = useState({ id: "", name: "", description: "" })
  const [newUser, setNewUser] = useState({ name: "", email: "", permissions: [] as string[] })
  const [isPermissionDialogOpen, setIsPermissionDialogOpen] = useState(false)
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false)

  const handleAddPermission = () => {
    if (newPermission.id && newPermission.name) {
      setPermissions([...permissions, { ...newPermission }])
      setNewPermission({ id: "", name: "", description: "" })
      setIsPermissionDialogOpen(false)
    }
  }

  const handleDeletePermission = (id: string) => {
    setPermissions(permissions.filter((p) => p.id !== id))
    // Remove this permission from all users
    setUsers(
      users.map((user) => ({
        ...user,
        permissions: user.permissions.filter((p) => p !== id),
      })),
    )
  }

  const handleAddUser = () => {
    if (newUser.name && newUser.email) {
      const id = Date.now().toString()
      setUsers([...users, { ...newUser, id }])
      setNewUser({ name: "", email: "", permissions: [] })
      setIsUserDialogOpen(false)
    }
  }

  const handleDeleteUser = (id: string) => {
    setUsers(users.filter((u) => u.id !== id))
  }

  const handlePermissionToggle = (permissionId: string, checked: boolean) => {
    if (checked) {
      setNewUser({
        ...newUser,
        permissions: [...newUser.permissions, permissionId],
      })
    } else {
      setNewUser({
        ...newUser,
        permissions: newUser.permissions.filter((p) => p !== permissionId),
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Shield className="w-8 h-8" />
          {t("authorizationTitle")}
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Permissions Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              {t("permissionsList")}
            </CardTitle>
            <Dialog open={isPermissionDialogOpen} onOpenChange={setIsPermissionDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  size="sm"
                  className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t("addPermission")}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{t("addNewPermission")}</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="permission-id">{t("permissionId")}</Label>
                    <Input
                      id="permission-id"
                      value={newPermission.id}
                      onChange={(e) => setNewPermission({ ...newPermission, id: e.target.value.toUpperCase() })}
                      placeholder={t("permissionIdPlaceholder")}
                    />
                  </div>
                  <div>
                    <Label htmlFor="permission-name">{t("permissionName")}</Label>
                    <Input
                      id="permission-name"
                      value={newPermission.name}
                      onChange={(e) => setNewPermission({ ...newPermission, name: e.target.value })}
                      placeholder={t("permissionNamePlaceholder")}
                    />
                  </div>
                  <div>
                    <Label htmlFor="permission-description">{t("description")}</Label>
                    <Textarea
                      id="permission-description"
                      value={newPermission.description}
                      onChange={(e) => setNewPermission({ ...newPermission, description: e.target.value })}
                      placeholder={t("descriptionPlaceholder")}
                      rows={3}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setIsPermissionDialogOpen(false)}>
                      {t("cancel")}
                    </Button>
                    <Button onClick={handleAddPermission}>{t("add")}</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {permissions.map((permission) => (
                <div key={permission.id} className="flex items-start justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="secondary" className="font-mono text-xs">
                        {permission.id}
                      </Badge>
                      <span className="font-medium">{permission.name}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{permission.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeletePermission(permission.id)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Users Section */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              {t("usersList")}
            </CardTitle>
            <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  size="sm"
                  className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t("addUser")}
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>{t("addNewUser")}</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="user-name">{t("userName")}</Label>
                    <Input
                      id="user-name"
                      value={newUser.name}
                      onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                      placeholder={t("userNamePlaceholder")}
                    />
                  </div>
                  <div>
                    <Label htmlFor="user-email">{t("userEmail")}</Label>
                    <Input
                      id="user-email"
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      placeholder={t("userEmailPlaceholder")}
                    />
                  </div>
                  <div>
                    <Label>{t("assignPermissions")}</Label>
                    <div className="space-y-2 mt-2 max-h-48 overflow-y-auto">
                      {permissions.map((permission) => (
                        <div key={permission.id} className="flex items-start space-x-2">
                          <Checkbox
                            id={`perm-${permission.id}`}
                            checked={newUser.permissions.includes(permission.id)}
                            onCheckedChange={(checked) => handlePermissionToggle(permission.id, checked as boolean)}
                          />
                          <div className="flex-1">
                            <Label htmlFor={`perm-${permission.id}`} className="text-sm font-medium">
                              {permission.name}
                            </Label>
                            <p className="text-xs text-muted-foreground">{permission.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setIsUserDialogOpen(false)}>
                      {t("cancel")}
                    </Button>
                    <Button onClick={handleAddUser}>{t("add")}</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {users.map((user) => (
                <div key={user.id} className="flex items-start justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">{user.name}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{user.email}</p>
                    <div className="flex flex-wrap gap-1">
                      {user.permissions.map((permId) => {
                        const permission = permissions.find((p) => p.id === permId)
                        return permission ? (
                          <Badge key={permId} variant="outline" className="text-xs">
                            {permission.name}
                          </Badge>
                        ) : null
                      })}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteUser(user.id)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
