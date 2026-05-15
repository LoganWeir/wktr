wktr() {
  local target; target=$(WKTR_SHELL=1 command wktr "$@"); local ec=$?
  [[ $ec -eq 0 && -n "$target" && -d "$target" ]] && cd "$target"
  return $ec
}
