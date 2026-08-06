import { Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation } from "@tanstack/react-query"
import { ChevronLeft, Dumbbell, MailCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ErrorState } from "@/components/common/ErrorState"
import { authService } from "@/services/authService"
import { getApiErrorMessage } from "@/lib/errors"

const forgotPasswordSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
})

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>

/** Works identically for all three roles - the backend flow is keyed on
 * email/user identity, not role (see PasswordResetService). Always shows
 * the same "check your email" confirmation regardless of whether the email
 * is actually registered, matching the backend's anti-enumeration design. */
export function ForgotPasswordPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({ resolver: zodResolver(forgotPasswordSchema) })

  const forgotPasswordMutation = useMutation({
    mutationFn: (values: ForgotPasswordFormValues) => authService.forgotPassword(values.email),
  })

  const onSubmit = (values: ForgotPasswordFormValues) => {
    forgotPasswordMutation.mutate(values)
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <Dumbbell className="mb-2 size-8 text-primary" aria-hidden="true" />
          <CardTitle className="text-xl">Forgot Password</CardTitle>
          <CardDescription>Enter your email and we'll send you a reset link</CardDescription>
        </CardHeader>
        <CardContent>
          {forgotPasswordMutation.isSuccess ? (
            <div className="flex flex-col items-center gap-3 py-2 text-center">
              <MailCheck className="size-8 text-primary" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">
                If an account with that email exists, a password reset link has been sent. Check your inbox.
              </p>
              <Button variant="ghost" size="sm" render={<Link to="/login" />} nativeButton={false}>
                <ChevronLeft className="size-4" />
                Back to sign in
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  aria-invalid={!!errors.email}
                  {...register("email")}
                />
                {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
              </div>

              {forgotPasswordMutation.isError && (
                <ErrorState
                  title="Couldn't send reset link"
                  message={getApiErrorMessage(forgotPasswordMutation.error, "Please try again.")}
                />
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting || forgotPasswordMutation.isPending}
              >
                {isSubmitting || forgotPasswordMutation.isPending ? "Sending..." : "Send Reset Link"}
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
