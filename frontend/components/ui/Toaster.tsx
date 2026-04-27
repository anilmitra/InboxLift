"use client";
import * as Toast from "@radix-ui/react-toast";
import { create } from "zustand";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "info";

interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastStore {
  toasts: ToastItem[];
  add: (message: string, type?: ToastType) => void;
  remove: (id: string) => void;
}

export const useToast = create<ToastStore>((set) => ({
  toasts: [],
  add: (message, type = "info") =>
    set((s) => ({
      toasts: [...s.toasts, { id: crypto.randomUUID(), message, type }],
    })),
  remove: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function toast(message: string, type: ToastType = "info") {
  useToast.getState().add(message, type);
}

const icons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="w-4 h-4 text-green-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
  info: <Info className="w-4 h-4 text-blue-500" />,
};

export function Toaster() {
  const { toasts, remove } = useToast();

  return (
    <Toast.Provider swipeDirection="right">
      {toasts.map((t) => (
        <Toast.Root
          key={t.id}
          open
          onOpenChange={(open) => !open && remove(t.id)}
          duration={4000}
          className={cn(
            "flex items-center gap-3 p-4 bg-white border border-border rounded-lg shadow-lg",
            "data-[state=open]:animate-fade-in",
            "data-[state=closed]:opacity-0",
            "max-w-sm w-full"
          )}
        >
          {icons[t.type]}
          <Toast.Description className="flex-1 text-sm text-foreground">
            {t.message}
          </Toast.Description>
          <Toast.Close asChild>
            <button className="text-muted-foreground hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          </Toast.Close>
        </Toast.Root>
      ))}
      <Toast.Viewport className="fixed bottom-4 right-4 flex flex-col gap-2 z-[9999] w-full max-w-sm" />
    </Toast.Provider>
  );
}
