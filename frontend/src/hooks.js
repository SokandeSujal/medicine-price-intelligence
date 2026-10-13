import { useEffect, useState } from 'react'
import { api } from './api'

export function useApi(path, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  useEffect(() => {
    if (!path) return
    let live = true
    setState((s) => ({ ...s, loading: true, error: null }))
    api(path).then((data) => live && setState({ data, loading: false, error: null }))
      .catch((error) => live && setState({ data: null, loading: false, error }))
    return () => { live = false }
  }, [path, ...deps])
  return state
}
