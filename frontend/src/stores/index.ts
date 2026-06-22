// ── Zustand Store ──
import { create } from 'zustand'
import type {
  User, ProfileDimension, LearningResource, ChatSession, ChatMessage, PathNode,
} from '@/types'

// ── Auth Store ──
interface AuthState {
  user: User | null
  token: string | null
  isLoggedIn: boolean
  login: (user: User, token: string) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoggedIn: false,
  login: (user, token) => {
    if (typeof window !== 'undefined') localStorage.setItem('auth_token', token)
    set({ user, token, isLoggedIn: true })
  },
  logout: () => {
    if (typeof window !== 'undefined') localStorage.removeItem('auth_token')
    set({ user: null, token: null, isLoggedIn: false })
  },
  setUser: (user) => set({ user }),
}))

// ── Profile Store ──
interface ProfileState {
  dimensions: ProfileDimension[]
  isComplete: boolean
  dialogueRound: number
  setDimensions: (dims: ProfileDimension[]) => void
  addDimension: (dim: ProfileDimension) => void
  setComplete: (v: boolean) => void
  setDialogueRound: (n: number) => void
  reset: () => void
}

export const useProfileStore = create<ProfileState>((set) => ({
  dimensions: [],
  isComplete: false,
  dialogueRound: 0,
  setDimensions: (dims) => set({ dimensions: dims }),
  addDimension: (dim) => set((s) => {
    const existing = s.dimensions.findIndex(d => d.name === dim.name)
    if (existing >= 0) {
      const dims = [...s.dimensions]
      dims[existing] = dim
      return { dimensions: dims }
    }
    return { dimensions: [...s.dimensions, dim] }
  }),
  setComplete: (v) => set({ isComplete: v }),
  setDialogueRound: (n) => set({ dialogueRound: n }),
  reset: () => set({ dimensions: [], isComplete: false, dialogueRound: 0 }),
}))

// ── Resources Store ──
interface ResourcesState {
  resources: LearningResource[]
  selectedIndex: number
  isGenerating: boolean
  setResources: (r: LearningResource[]) => void
  addResources: (r: LearningResource[]) => void
  setSelected: (i: number) => void
  setGenerating: (v: boolean) => void
  clear: () => void
}

export const useResourcesStore = create<ResourcesState>((set) => ({
  resources: [],
  selectedIndex: 0,
  isGenerating: false,
  setResources: (r) => set({ resources: r, selectedIndex: 0 }),
  addResources: (r) => set((s) => ({ resources: [...s.resources, ...r] })),
  setSelected: (i) => set({ selectedIndex: i }),
  setGenerating: (v) => set({ isGenerating: v }),
  clear: () => set({ resources: [], selectedIndex: 0, isGenerating: false }),
}))

// ── Learning Path Store ──
interface PathState {
  nodes: PathNode[]
  progress: number
  setNodes: (n: PathNode[]) => void
  setProgress: (p: number) => void
  toggleNode: (index: number) => void
  clear: () => void
}

export const usePathStore = create<PathState>((set) => ({
  nodes: [],
  progress: 0,
  setNodes: (n) => set({ nodes: n }),
  setProgress: (p) => set({ progress: p }),
  toggleNode: (index) => set((s) => {
    const nodes = [...s.nodes]
    nodes[index] = { ...nodes[index], completed: !nodes[index].completed }
    const completed = nodes.filter(n => n.completed).length
    return { nodes, progress: nodes.length > 0 ? completed / nodes.length : 0 }
  }),
  clear: () => set({ nodes: [], progress: 0 }),
}))
