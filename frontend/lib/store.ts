import { create } from "zustand";
import { persist } from "zustand/middleware";
import Cookies from "js-cookie";

interface User {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  timezone: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      login: (accessToken, refreshToken, user) => {
        Cookies.set("access_token", accessToken, { expires: 1, sameSite: "Strict" });
        Cookies.set("refresh_token", refreshToken, { expires: 30, sameSite: "Strict" });
        set({ user, isAuthenticated: true });
      },
      logout: () => {
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: "inboxlift-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

interface UIState {
  sidebarCollapsed: boolean;
  selectedAccountId: number | null;
  toggleSidebar: () => void;
  setSelectedAccount: (id: number | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  selectedAccountId: null,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSelectedAccount: (id) => set({ selectedAccountId: id }),
}));
