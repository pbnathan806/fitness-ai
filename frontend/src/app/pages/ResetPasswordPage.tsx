import { Link, useSearchParams } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation } from "@tanstack/react-query"
import { CheckCircle2, ChevronLeft, Dumbbell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ErrorState } from "@/components/common/ErrorState"
import { authService } from "@/services/authService"
import { getApiErrorMessage } from "@/lib/errors"

const resetPasswordSchema = z
  .object({
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your new password"),
  })
  .refine((values) => values.new_password === values.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

/** Works identically for all three roles - reset is keyed on the token
 * (which resolves to a user, not a role) rather than any role-specific
 * logic. Reached via the link emailed by the backend's Resend integration:
 * `{FRONTEND_BASE_URL}/reset-password?token=...`. */
export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token")

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({ resolver: zodResolver(resetPasswordSchema) })

  const resetPasswordMutation = useMutation({
    mutationFn: (values: ResetPasswordFormValues) => authService.resetPassword(token!, values.new_password),
  })

  const onSubmit = (values: ResetPasswordFormValues) => {
    resetPasswordMutation.mutate(values)
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <Dumbbell className="mb-2 size-8 text-primary" aria-hidden="true" />
          <CardTitle className="text-xl">Reset Password</CardTitle>
          <CardDescription>Choose a new password for your account</CardDescription>
        </CardHeader>
        <CardContent>
          {!token ? (
            <div className="space-y-4 text-center">
              <ErrorState
                title="Invalid reset link"
                message="This password reset link is missing or malformed. Request a new one below."
              />
              <Button
                variant="outline"
                className="w-full"
                render={<Link to="/forgot-password" />}
                nativeButton={false}
              >
                Request a new link
              </Button>
            </div>
          ) : resetPasswordMutation.isSuccess ? (
            <div className="flex flex-col items-center gap-3 py-2 text-center">
              <CheckCircle2 className="size-8 text-primary" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">
                Your password has been reset successfully. You can now sign in with your new password.
              </p>
              <Button className="w-full" render={<Link to="/login" />} nativeButton={false}>
                Sign in
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new_password">New Password</Label>
                <Input
                  id="new_password"
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={!!errors.new_password}
                  {...register("new_password")}
                />
                {errors.new_password && (
                  <p className="text-sm text-destructive">{errors.new_password.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm_password">Confirm New Password</Label>
                <Input
                  id="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={!!errors.confirm_password}
                  {...register("confirm_password")}
                />
                {errors.confirm_password && (
                  <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
                )}
              </div>

              {resetPasswordMutation.isError && (
                <ErrorState
                  title="Couldn't reset password"
                  message={getApiErrorMessage(
                    resetPasswordMutation.error,
                    "This link may have expired. Request a new one.",
                  )}
                />
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting || resetPasswordMutation.isPending}
              >
                {isSubmitting || resetPasswordMutation.isPending ? "Resetting..." : "Reset Password"}
              </Button>

              <Button variant="ghost" size="sm" className="w-full" render={<Link to="/login" />} nativeButton={false}>
                <ChevronLeft className="size-4" />
                Back to sign in
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
