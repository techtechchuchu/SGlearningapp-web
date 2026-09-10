# SG Learning Web

SG 오답노트의 **독립된 학생용 웹 프로젝트**입니다.

- 기존 운영 저장소 `techtechchuchu/SG-wrong-noteapp`은 수정하지 않습니다.
- 현재 버전은 예시 데이터 기반 UI 데모입니다. 로그인 및 운영 Supabase DB 연결은 없습니다.
- 체험 기록은 메모리에만 보관되어 새로고침하면 초기화됩니다. 실제 학원 제출 기능이 아닙니다.
- 학생 홈, 오답 입력·조회·수정·삭제, 복습 완료 표시, 모바일 반응형 화면을 제공합니다.
- X-패턴은 실제 학교별 시험/offset 정보 확인 전까지 입력을 비활성화했습니다.

## 기술

React 19 + TypeScript + Next.js App Router 호환 구조. 현재 미리보기/배포 빌드는 Vinext와 Cloudflare Workers를 사용합니다. 표준 Next.js 배포로 전환할 때에는 별도 검증이 필요합니다.

## 실행

Node.js 22.13 이상과 package.json의 packageManager에 지정된 pnpm을 사용합니다.

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm build
```

## 운영 연결 전 확인

1. 기존 로그인 코드와 users 테이블 권한 확인.
2. 검증된 이메일 기반 복구와 학생/선생님/관리자 권한 설계.
3. 운영 데이터 대신 별도 테스트 환경에서 저장 응답/재조회와 중복 제출 검증.
4. 여러 교재 명단 분리와 X-패턴 학교별 offset 왕복 변환 검증.
5. 기존 Streamlit과의 호환성을 확인한 후 운영 연결.

service_role 및 AI API 키는 클라이언트나 저장소에 넣지 않습니다. 운영 DB에 대한 변경은 이 프로젝트 초기 구성에 포함되지 않습니다.

## 검증 범위

프로덕션 빌드와 TypeScript 검사를 수행합니다. 브라우저 E2E 및 WebMCP 런타임 검증은 수행하지 않았습니다.
