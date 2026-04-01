#!/usr/bin/env bash
set -euo pipefail

COMMON_SKILLS=(
  agentmail
  shortcut
  git-essentials
  git-commit
)

BACKEND_SKILLS=(
  nodejs-nestjs-backend
)

FRONTEND_SKILLS=(
  frontend-react-nextjs
)

list_bundles() {
  printf '%s\n' backend frontend full-stack
}

bundle_exists() {
  local bundle="$1"
  case "$bundle" in
    backend|frontend|full-stack) return 0 ;;
    *) return 1 ;;
  esac
}

bundle_agents() {
  local bundle="$1"
  case "$bundle" in
    backend) printf '%s\n' main backend ;;
    frontend) printf '%s\n' main frontend ;;
    full-stack) printf '%s\n' main backend frontend ;;
    *)
      echo "Unknown bundle: $bundle" >&2
      return 1
      ;;
  esac
}

agent_role() {
  local bundle="$1"
  local agent="$2"
  case "$bundle:$agent" in
    backend:main) printf '%s\n' backend-lead ;;
    backend:backend) printf '%s\n' backend ;;
    frontend:main) printf '%s\n' frontend-lead ;;
    frontend:frontend) printf '%s\n' frontend ;;
    full-stack:main) printf '%s\n' full-stack ;;
    full-stack:backend) printf '%s\n' backend ;;
    full-stack:frontend) printf '%s\n' frontend ;;
    *)
      echo "Unknown bundle/agent combination: $bundle / $agent" >&2
      return 1
      ;;
  esac
}

append_unique() {
  local item
  for item in "$@"; do
    [[ -z "$item" ]] && continue
    case " ${APPEND_UNIQUE_RESULT[*]:-} " in
      *" $item "*) ;;
      *) APPEND_UNIQUE_RESULT+=("$item") ;;
    esac
  done
}

agent_skills() {
  local bundle="$1"
  local agent="$2"
  local role
  role="$(agent_role "$bundle" "$agent")"

  APPEND_UNIQUE_RESULT=()
  append_unique "${COMMON_SKILLS[@]}"

  case "$role" in
    backend|backend-lead)
      append_unique "${BACKEND_SKILLS[@]}"
      ;;
    frontend|frontend-lead)
      append_unique "${FRONTEND_SKILLS[@]}"
      ;;
    full-stack)
      append_unique "${BACKEND_SKILLS[@]}" "${FRONTEND_SKILLS[@]}"
      ;;
  esac

  printf '%s\n' "${APPEND_UNIQUE_RESULT[@]}"
}

bundle_skills() {
  local bundle="$1"
  local agent

  APPEND_UNIQUE_RESULT=()
  while IFS= read -r agent; do
    while IFS= read -r skill; do
      append_unique "$skill"
    done < <(agent_skills "$bundle" "$agent")
  done < <(bundle_agents "$bundle")

  printf '%s\n' "${APPEND_UNIQUE_RESULT[@]}"
}

agent_prompt() {
  local bundle="$1"
  local agent="$2"
  local role
  role="$(agent_role "$bundle" "$agent")"

  case "$role" in
    backend)
      cat <<'EOF'
Own backend delivery for this Clawbot workspace. Focus on Node.js and NestJS services, APIs, validation, auth, data access, observability, and backend testing. Reuse the shared Git, Shortcut, and AgentMail skills when coordination or delivery workflows need them.
EOF
      ;;
    backend-lead)
      cat <<'EOF'
Lead a backend-oriented Clawbot setup. You can handle end-to-end work, but your strongest focus is Node.js and NestJS backend execution, API review, database-integrated features, and operational safety. Reuse shared Git, Shortcut, and AgentMail skills for coordination.
EOF
      ;;
    frontend)
      cat <<'EOF'
Own frontend delivery for this Clawbot workspace. Focus on HTML, CSS, Tailwind CSS, React, Next.js, UX quality, accessibility, responsive behavior, and frontend performance. Reuse the shared Git, Shortcut, and AgentMail skills when team workflows need them.
EOF
      ;;
    frontend-lead)
      cat <<'EOF'
Lead a frontend-oriented Clawbot setup. You can handle end-to-end work, but your strongest focus is React, Next.js, HTML, CSS, Tailwind CSS, accessibility, responsive interfaces, and polished UX. Reuse shared Git, Shortcut, and AgentMail skills for coordination.
EOF
      ;;
    full-stack)
      cat <<'EOF'
Lead this full-stack Clawbot setup. Coordinate delivery across frontend and backend work, use the shared Git, Shortcut, and AgentMail skills for workflow automation, and route deep implementation to the dedicated backend and frontend agents when that keeps work clearer.
EOF
      ;;
    *)
      echo "Unknown role for prompt generation: $role" >&2
      return 1
      ;;
  esac
}
