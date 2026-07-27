import { useMutation } from "@tanstack/react-query"
import { useAuth } from "@/hooks/useAuth"

interface LoginVariables {
  email: string
  password: string
}

export function useLogin() {
  const { login } = useAuth()

  return useMutation({
    mutationFn: ({ email, password }: LoginVariables) => login(email, password),
  })
}
