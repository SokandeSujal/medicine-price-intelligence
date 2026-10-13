export const ease = [0.22, 1, 0.36, 1]
export const pageMotion = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: { duration: 0.32, ease },
}
export const cardMotion = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease },
  whileHover: { y: -4, transition: { duration: 0.18, ease } },
}
export const stagger = {
  animate: { transition: { staggerChildren: 0.065 } },
}
