import type { NavigationGroup } from '@/types'

interface BuildTreeOptions {
  omitEmptyChildren?: boolean
}

export function buildNavigationTree(
  flat: NavigationGroup[],
  options: BuildTreeOptions = {}
): NavigationGroup[] {
  const map = new Map<string, NavigationGroup>()
  const roots: NavigationGroup[] = []

  flat.forEach(group => map.set(group.id, { ...group, children: [] }))
  map.forEach(group => {
    if (group.parent_id && map.has(group.parent_id)) {
      map.get(group.parent_id)!.children!.push(group)
    } else {
      roots.push(group)
    }
  })

  const sortTree = (nodes: NavigationGroup[]): NavigationGroup[] =>
    [...nodes].sort((a, b) => a.sort_order - b.sort_order).map(node => {
      const children = node.children?.length ? sortTree(node.children) : undefined
      return {
        ...node,
        children: options.omitEmptyChildren ? children : children ?? []
      }
    })

  return sortTree(roots)
}
