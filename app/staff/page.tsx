"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import "./staff.css";
import {
  Bell, BookOpen, CalendarDays, Check, ChevronDown, ClipboardList,
  Download, FileSpreadsheet, GraduationCap, LayoutDashboard, LockKeyhole,
  LogOut, Menu, NotebookTabs, Printer, School, Search, Settings,
  ShieldCheck, Upload, UserCog, Users, X, AlertTriangle, Pencil,
  ArrowRightLeft, UserRoundCheck, Database, Megaphone,
} from "lucide-react";
import { toast, Toaster } from "sonner";

type Role = "teacher" | "admin";
type MenuKey =
  | "dashboard" | "answers" | "weekly" | "exams" | "missing" | "signup"
  | "classes" | "paper" | "print" | "resets" | "roster" | "students"
  | "books" | "examAdmin" | "notices" | "records" | "backup";

type Student = {id:number;name:string;teacher:string;className:string;school:string;grade:string;books:string[];joined:boolean;submitted:number;last:string};
type Answer = {id:number;student:string;book:string;problems:string;memo:string;created:string;kind:"교재"|"학교 기출"};

const TEACHERS=["이주백.T","박병민.T","노대근.T"];
const STUDENTS:Student[]=[
  {id:1,name:"김민준",teacher:"이주백.T",className:"월금일(앞) 고1 내신심화반",school:"신정고",grade:"고1",books:["X-패턴 공통수학2","UNIT N제 공통수학2"],joined:true,submitted:10,last:"09.10 22:14"},
  {id:2,name:"박서윤",teacher:"이주백.T",className:"월금일(앞) 고1 내신심화반",school:"중앙고",grade:"고1",books:["X-패턴 공통수학2"],joined:true,submitted:6,last:"09.10 21:48"},
  {id:3,name:"이현우",teacher:"박병민.T",className:"화목토일(앞) 고2 미적분1",school:"삼산고",grade:"고2",books:["미적분1 고쟁이"],joined:false,submitted:0,last:"-"},
  {id:4,name:"최유진",teacher:"박병민.T",className:"화목토일(앞) 고2 미적분1",school:"학성고",grade:"고2",books:["미적분1 고쟁이","X-패턴 미적분1"],joined:true,submitted:4,last:"09.09 19:02"},
  {id:5,name:"정도윤",teacher:"노대근.T",className:"수금일 고2 기하반",school:"무거고",grade:"고2",books:["기하 쎈"],joined:true,submitted:0,last:"09.03 17:31"},
  {id:6,name:"한지우",teacher:"노대근.T",className:"수금일 고2 기하반",school:"대현고",grade:"고2",books:["기하 쎈"],joined:true,submitted:8,last:"09.10 20:36"},
];
const ANSWERS:Answer[]=[
  {id:101,student:"김민준",book:"UNIT N제 공통수학2",problems:"9, 12, 18",memo:"정의역 조건 재확인",created:"2026.09.10 22:14",kind:"교재"},
  {id:102,student:"박서윤",book:"X-패턴 공통수학2",problems:"24 신정고: 8, 12",memo:"학교별 번호로 표시",created:"2026.09.10 21:48",kind:"교재"},
  {id:103,student:"한지우",book:"기하 쎈",problems:"412, 416, 420",memo:"정사영 넓이",created:"2026.09.10 20:36",kind:"교재"},
  {id:104,student:"최유진",book:"2025 삼산고 미적분1",problems:"18, 19",memo:"채점결과 파일 자동 반영",created:"2026.09.09 19:02",kind:"학교 기출"},
];

const teacherMenus:{key:MenuKey;label:string;icon:typeof Users}[]=[
  {key:"dashboard",label:"운영 대시보드",icon:LayoutDashboard},{key:"answers",label:"전체 오답 현황",icon:ClipboardList},
  {key:"weekly",label:"주간 제출 현황",icon:CalendarDays},{key:"exams",label:"학교 기출 오답",icon:School},
  {key:"missing",label:"미제출 학생",icon:AlertTriangle},{key:"signup",label:"가입 현황",icon:UserRoundCheck},
  {key:"classes",label:"내 반 학생",icon:Users},{key:"paper",label:"오답 Paper",icon:FileSpreadsheet},
  {key:"print",label:"출력 관리",icon:Printer},{key:"resets",label:"비밀번호 요청",icon:LockKeyhole},
];
const adminMenus:{key:MenuKey;label:string;icon:typeof Users}[]=[
  {key:"dashboard",label:"관리자 대시보드",icon:LayoutDashboard},{key:"resets",label:"비밀번호 재설정",icon:LockKeyhole},
  {key:"roster",label:"학생 명단 관리",icon:FileSpreadsheet},{key:"students",label:"학생 통합 관리",icon:UserCog},
  {key:"books",label:"교재 관리",icon:BookOpen},{key:"examAdmin",label:"학교 기출 관리",icon:School},
  {key:"notices",label:"공지사항",icon:Megaphone},{key:"records",label:"오답 기록 수정",icon:Pencil},
  {key:"backup",label:"계정 복구·백업",icon:Database},{key:"print",label:"전체 출력 관리",icon:Printer},
];

const titleMap:Record<MenuKey,[string,string]>={
  dashboard:["운영 대시보드","오늘 확인할 학습 현황을 한눈에 봅니다."],answers:["전체 오답 현황","담당 학생의 교재별 오답을 조회합니다."],weekly:["주간 제출 현황","월요일부터 일요일까지의 제출을 집계합니다."],exams:["학교 기출 오답 현황","직접 입력과 채점결과 파일 기록을 확인합니다."],missing:["미제출 학생","이번 주 아직 오답을 제출하지 않은 학생입니다."],signup:["학생 가입 현황","명단과 실제 계정을 비교합니다."],classes:["내 반 학생","담당 반별 학생과 교재를 확인합니다."],paper:["오답 Paper 만들기","선택 학생의 PDF 생성용 엑셀을 만듭니다."],print:["출력 관리","오답 Paper 출력 대기와 완료 상태를 관리합니다."],resets:["비밀번호 재설정 요청","학생의 초기화 요청을 처리합니다."],roster:["학생 명단 관리","최종 명단 엑셀 업로드와 현재 명단을 관리합니다."],students:["학생 통합 관리","이름·반·담당·학교·학년·교재·계정을 관리합니다."],books:["교재 관리","교재 등록·수정·사용 여부를 관리합니다."],examAdmin:["학교 기출 관리","시험 정보와 채점결과 업로드를 관리합니다."],notices:["공지사항 관리","학생·선생님에게 표시할 공지를 관리합니다."],records:["오답 기록 수정","잘못 선택한 교재와 X-패턴 학교를 바로잡습니다."],backup:["계정 복구·백업","회원목록 복구, 계정 이전, 엑셀 백업을 처리합니다."],
};

function csvDownload(filename:string, rows:Record<string,unknown>[]){
  if(!rows.length){toast.error("내보낼 내용이 없습니다.");return}
  const keys=Object.keys(rows[0]);
  const esc=(v:unknown)=>`"${String(v??"").replaceAll('"','""')}"`;
  const body="\ufeff"+[keys.join(","),...rows.map(r=>keys.map(k=>esc(r[k])).join(","))].join("\n");
  const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([body],{type:"text/csv;charset=utf-8"}));a.download=filename;a.click();URL.revokeObjectURL(a.href);
}

function DemoTable({rows,kind="students",selected,setSelected}:{rows:(Student|Answer)[];kind?:"students"|"answers";selected?:number[];setSelected?:(v:number[])=>void}){
  if(!rows.length)return <div className="staff-empty"><Search/><b>조건에 맞는 결과가 없습니다.</b><span>필터를 바꿔 다시 확인해 주세요.</span></div>;
  return <div className="table-scroll"><table className="data-table"><thead><tr>{selected&&<th>선택</th>}{kind==="students"?<><th>학생</th><th>학교·학년</th><th>담당·반</th><th>교재</th><th>가입</th><th>제출</th><th>최근 제출</th></>:<><th>작성일시</th><th>학생</th><th>구분</th><th>교재·시험</th><th>문제번호</th><th>비고</th></>}</tr></thead><tbody>{rows.map(row=>{const s=row as Student,a=row as Answer;return <tr key={row.id}>{selected&&<td><input aria-label={`${kind==="students"?s.name:a.student} 선택`} type="checkbox" checked={selected.includes(row.id)} onChange={e=>setSelected?.(e.target.checked?[...selected,row.id]:selected.filter(x=>x!==row.id))}/></td>}{kind==="students"?<><td><b>{s.name}</b></td><td>{s.school}<small>{s.grade}</small></td><td>{s.teacher}<small>{s.className}</small></td><td>{s.books.map(b=><span className="tag" key={b}>{b}</span>)}</td><td><span className={s.joined?"status ok":"status wait"}>{s.joined?"가입 완료":"미가입"}</span></td><td><b>{s.submitted}</b>문제</td><td>{s.last}</td></>:<><td>{a.created}</td><td><b>{a.student}</b></td><td><span className="tag">{a.kind}</span></td><td>{a.book}</td><td><b>{a.problems}</b></td><td>{a.memo}</td></>}</tr>})}</tbody></table></div>
}

export default function StaffPage(){
  const [role,setRole]=useState<Role>("teacher"),[teacher,setTeacher]=useState(TEACHERS[0]),[menu,setMenu]=useState<MenuKey>("dashboard"),[query,setQuery]=useState(""),[mobile,setMobile]=useState(false),[selected,setSelected]=useState<number[]>([]),[week,setWeek]=useState("2026-09-07"),[modal,setModal]=useState<string|null>(null);
  const [students,setStudents]=useState(STUDENTS),[answers,setAnswers]=useState(ANSWERS),[printed,setPrinted]=useState<number[]>([102]),[books,setBooks]=useState(["공통수학2 고쟁이","공통수학2 RPM","UNIT N제 공통수학2","X-패턴 공통수학2","미적분1 고쟁이","X-패턴 미적분1","기하 쎈"]),[notices,setNotices]=useState(["오답 입력 후 저장 완료 문구를 꼭 확인해 주세요.","이번 주 오답 Paper는 일요일에 출력됩니다."]);
  const visibleStudents=useMemo(()=>students.filter(s=>(role==="admin"||s.teacher===teacher)&&(!query||[s.name,s.school,s.className,...s.books].join(" ").includes(query))),[students,role,teacher,query]);
  const visibleAnswers=useMemo(()=>answers.filter(a=>role==="admin"||visibleStudents.some(s=>s.name===a.student)).filter(a=>!query||Object.values(a).join(" ").includes(query)),[answers,role,visibleStudents,query]);
  const menus=role==="teacher"?teacherMenus:adminMenus;
  const missing=visibleStudents.filter(s=>s.submitted===0),joined=visibleStudents.filter(s=>s.joined).length,pending=visibleStudents.filter(s=>!s.joined).length;
  function changeRole(next:Role){setRole(next);setMenu("dashboard");setSelected([]);setQuery("")}
  function done(message:string){setModal(null);toast.success(message+" · 체험 화면에만 반영됐습니다.")}
  function menuClick(k:MenuKey){setMenu(k);setMobile(false);setSelected([])}
  return <div className="staff-app"><Toaster position="top-center"/>
    <aside className={mobile?"staff-sidebar open":"staff-sidebar"}><div className="staff-logo"><span>SG</span><div>SG고등관<b>{role==="teacher"?"선생님 관리":"전체 관리자"}</b></div><button onClick={()=>setMobile(false)} aria-label="메뉴 닫기"><X/></button></div><nav>{menus.map(({key,label,icon:Icon})=><button key={key} className={menu===key?"active":""} onClick={()=>menuClick(key)}><Icon/>{label}{key==="resets"&&<i>2</i>}</button>)}</nav><div className="staff-side-bottom"><Link href="/"><GraduationCap/>학생 화면 보기</Link><button onClick={()=>toast("체험판에서는 로그인 상태가 없습니다.")}><LogOut/>로그아웃</button></div></aside>
    {mobile&&<button className="staff-overlay" onClick={()=>setMobile(false)} aria-label="메뉴 닫기"/>}
    <section className="staff-main"><header className="staff-top"><button className="mobile-menu" onClick={()=>setMobile(true)} aria-label="메뉴 열기"><Menu/></button><div className="role-switch"><button className={role==="teacher"?"active":""} onClick={()=>changeRole("teacher")}>선생님</button><button className={role==="admin"?"active":""} onClick={()=>changeRole("admin")}><ShieldCheck/>전체 관리자</button></div>{role==="teacher"&&<label className="teacher-select"><span>로그인 계정</span><select value={teacher} onChange={e=>setTeacher(e.target.value)}>{TEACHERS.map(t=><option key={t}>{t}</option>)}</select><ChevronDown/></label>}<button className="bell" aria-label="알림"><Bell/><i>2</i></button></header>
      <main className="staff-content"><div className="demo-banner"><span className="pill">기능 이식본</span>운영 데이터에 연결되지 않은 관리자 체험 화면입니다. 저장·삭제·초기화는 실제 DB에 반영되지 않습니다.</div><div className="staff-heading"><div><p>{role==="teacher"?teacher:"전체 관리자"}</p><h1>{titleMap[menu][0]}</h1><span>{titleMap[menu][1]}</span></div><div className="heading-actions"><label><Search/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="학생·학교·반 검색"/></label><button className="staff-primary" onClick={()=>csvDownload(`${titleMap[menu][0]}.csv`,(menu==="answers"||menu==="exams"?visibleAnswers:visibleStudents) as unknown as Record<string,unknown>[])}><Download/>엑셀용 CSV</button></div></div>
        {menu==="dashboard"&&<><div className="staff-stats"><section><span>담당 학생</span><strong>{visibleStudents.length}<small>명</small></strong><Users/></section><section><span>이번 주 제출</span><strong>{visibleStudents.length-missing.length}<small>명</small></strong><ClipboardList/></section><section className="warn"><span>미제출 학생</span><strong>{missing.length}<small>명</small></strong><AlertTriangle/></section><section><span>가입 완료</span><strong>{joined}<small>명</small></strong><UserRoundCheck/></section></div><div className="staff-grid"><section className="staff-card wide"><CardHead title="최근 오답 제출" action="전체 보기" onClick={()=>menuClick("answers")}/><DemoTable rows={visibleAnswers.slice(0,4)} kind="answers"/></section><section className="staff-card"><CardHead title="이번 주 확인"/><div className="check-list"><button onClick={()=>menuClick("missing")}><span><AlertTriangle/>미제출 학생</span><b>{missing.length}명</b></button><button onClick={()=>menuClick("signup")}><span><UserRoundCheck/>미가입 학생</span><b>{pending}명</b></button><button onClick={()=>menuClick("resets")}><span><LockKeyhole/>초기화 요청</span><b>2건</b></button><button onClick={()=>menuClick("print")}><span><Printer/>출력 대기</span><b>{Math.max(0,visibleAnswers.length-printed.length)}건</b></button></div></section></div></>}
        {menu==="answers"&&<section className="staff-card"><FilterRow teacher={teacher} week={week} setWeek={setWeek}/><DemoTable rows={visibleAnswers.filter(a=>a.kind==="교재")} kind="answers"/></section>}
        {menu==="weekly"&&<section className="staff-card"><FilterRow teacher={teacher} week={week} setWeek={setWeek}/><div className="summary-line"><b>제출 {visibleStudents.length-missing.length}명</b><span>미제출 {missing.length}명</span><span>총 {visibleStudents.reduce((n,s)=>n+s.submitted,0)}문제</span></div><DemoTable rows={visibleStudents}/></section>}
        {menu==="exams"&&<section className="staff-card"><div className="toolbar"><button className="staff-primary" onClick={()=>setModal("gradeUpload")}><Upload/>채점결과 엑셀 업로드</button><span>같은 파일은 해시로 중복 업로드를 차단합니다.</span></div><DemoTable rows={visibleAnswers.filter(a=>a.kind==="학교 기출")} kind="answers"/></section>}
        {menu==="missing"&&<section className="staff-card"><FilterRow teacher={teacher} week={week} setWeek={setWeek}/><div className="callout warning"><AlertTriangle/><div><b>이번 주 미제출 {missing.length}명</b><span>명단 학생 기준이며 한 문제 이상 저장하면 제출로 집계됩니다.</span></div></div><DemoTable rows={missing}/></section>}
        {(menu==="signup"||menu==="classes")&&<section className="staff-card"><div className="summary-line"><b>가입 완료 {joined}명</b><span>미가입 {pending}명</span><span>쉼표로 등록된 여러 교재도 각각 매칭</span></div><DemoTable rows={visibleStudents}/></section>}
        {menu==="paper"&&<section className="staff-card"><div className="paper-form"><Field label="반"><select><option>{visibleStudents[0]?.className||"등록된 반 없음"}</option></select></Field><Field label="교재"><select>{books.map(b=><option key={b}>{b}</option>)}</select></Field><Field label="월"><select><option>9월</option></select></Field><Field label="주차"><select><option>2주차</option></select></Field></div><p className="muted">학생을 선택하면 PDF 상단 제목·파일명·문제번호가 포함된 생성용 파일을 만듭니다.</p><DemoTable rows={visibleStudents} selected={selected} setSelected={setSelected}/><div className="sticky-actions"><span>{selected.length}명 선택</span><button className="staff-primary" onClick={()=>selected.length?done("오답 Paper 생성용 CSV를 준비했습니다"):toast.error("학생을 선택해 주세요.")}><FileSpreadsheet/>생성용 파일 만들기</button></div></section>}
        {menu==="print"&&<section className="staff-card"><div className="toolbar"><button onClick={()=>{setPrinted(visibleAnswers.map(a=>a.id));done("선택 기록을 출력 완료 처리했습니다")}}><Check/>모두 출력 완료</button><span>Paper 파일을 내려받으면 출력 대기 목록에 자동 등록됩니다.</span></div><div className="print-list">{visibleAnswers.map(a=><article key={a.id}><button className={printed.includes(a.id)?"print-check checked":"print-check"} onClick={()=>setPrinted(p=>p.includes(a.id)?p.filter(x=>x!==a.id):[...p,a.id])}><Check/></button><div><b>{a.student} · {a.book}</b><span>{a.problems}번 · {a.created}</span></div><label>메모<input placeholder="출력 메모"/></label><button onClick={()=>{setAnswers(v=>v.filter(x=>x.id!==a.id));toast.success("체험 목록에서 삭제했습니다.")}}><X/></button></article>)}</div></section>}
        {menu==="resets"&&<section className="staff-card"><div className="callout warning"><LockKeyhole/><div><b>처리 대기 2건</b><span>관리자는 학생이 직접 바꾼 비밀번호를 볼 수 없고 새 임시 비밀번호만 발급합니다.</span></div></div>{["김민준","최유진"].map(name=><div className="request-row" key={name}><div><b>{name}</b><span>2026.09.10 요청 · 담당 {students.find(s=>s.name===name)?.teacher}</span></div><button onClick={()=>setModal(`reset:${name}`)}>임시 비밀번호 발급</button></div>)}</section>}
        {menu==="roster"&&<section className="staff-card"><div className="upload-zone"><Upload/><h3>최종 학생명단 엑셀 업로드</h3><p>학생명단 시트의 반명·담당선생님·학생명·학교명·학년·매칭교재를 읽습니다.</p><button onClick={()=>setModal("rosterUpload")}>파일 선택 및 검증</button><small>전체 교체는 미리보기와 확인 후에만 가능합니다.</small></div><DemoTable rows={visibleStudents}/></section>}
        {menu==="students"&&<section className="staff-card"><div className="toolbar"><button onClick={()=>setModal("transfer")}><ArrowRightLeft/>오답 계정 이전</button><button onClick={()=>setModal("studentEdit")}><UserCog/>학생 정보 수정</button><span>이름 변경 시 계정→오답→명단의 외래키 순서를 지킵니다.</span></div><DemoTable rows={visibleStudents} selected={selected} setSelected={setSelected}/></section>}
        {menu==="books"&&<section className="staff-card"><div className="toolbar"><button className="staff-primary" onClick={()=>setModal("bookAdd")}><BookOpen/>교재 등록</button><span>교재명 변경 시 오답과 출력 목록의 이름도 함께 변경합니다.</span></div><div className="master-list">{books.map((b,i)=><article key={b}><span className="master-icon"><BookOpen/></span><div><b>{b}</b><span>{i<2?"고1 · 공통수학":"고2 · 수학"} · 사용 중</span></div><button onClick={()=>setModal(`bookEdit:${b}`)}>수정</button><button onClick={()=>{setBooks(v=>v.filter(x=>x!==b));toast.success("체험 목록에서 사용 중지했습니다.")}}>사용 중지</button></article>)}</div></section>}
        {menu==="examAdmin"&&<section className="staff-card"><div className="toolbar"><button className="staff-primary" onClick={()=>setModal("examAdd")}><School/>학교 기출 등록</button><button onClick={()=>setModal("gradeUpload")}><Upload/>채점결과 업로드</button></div><div className="master-list"><article><span className="master-icon"><School/></span><div><b>2025 삼산고 미적분1 1학기중간</b><span>21문항 · 사용 중 · 채점결과 1회 반영</span></div><button onClick={()=>setModal("examEdit")}>수정</button><button>사용 중지</button></article></div></section>}
        {menu==="notices"&&<section className="staff-card"><div className="toolbar"><button className="staff-primary" onClick={()=>setModal("noticeAdd")}><Megaphone/>새 공지</button></div><div className="master-list">{notices.map((n,i)=><article key={n}><span className="master-icon"><Megaphone/></span><div><b>{n}</b><span>{i?"선생님 대상":"전체 대상"} · 사용 중</span></div><button onClick={()=>setModal("noticeEdit")}>수정</button><button onClick={()=>setNotices(v=>v.filter(x=>x!==n))}>사용 중지</button></article>)}</div></section>}
        {menu==="records"&&<section className="staff-card"><div className="callout"><Pencil/><div><b>교재 변경 및 X-패턴 학교 재지정</b><span>원래 시험지 번호를 유지한 채 새 학교 offset으로 다시 변환합니다.</span></div></div><DemoTable rows={visibleAnswers} kind="answers" selected={selected} setSelected={setSelected}/><div className="sticky-actions"><span>{selected.length}건 선택</span><button onClick={()=>setModal("recordEdit")}>선택 기록 수정</button></div></section>}
        {menu==="backup"&&<section className="staff-grid"><section className="staff-card"><CardHead title="회원목록 일괄 복구"/><p className="muted">기존 계정은 삭제하지 않고 학년과 임시 비밀번호를 갱신합니다.</p><button className="staff-primary block" onClick={()=>setModal("restore")}><Upload/>회원목록 엑셀 업로드</button></section><section className="staff-card"><CardHead title="데이터 백업"/><p className="muted">학생 계정·명단·일반 오답·학교 기출·출력 현황을 파일로 보관합니다.</p><button className="staff-primary block" onClick={()=>csvDownload("SG고등관_학생명단.csv",students as unknown as Record<string,unknown>[])}><Download/>현재 명단 다운로드</button></section></section>}
      </main>
    </section>
    {modal&&<DemoModal title={modalTitle(modal)} onClose={()=>setModal(null)} onSave={()=>{
      if(modal==="bookAdd")setBooks(v=>[...v,"새 교재 (체험)"]);if(modal==="noticeAdd")setNotices(v=>["새 공지사항 (체험)",...v]);if(modal==="studentEdit")setStudents(v=>v.map((s,i)=>i===0?{...s,school:"신정고 (수정됨)"}:s));done(modal.startsWith("reset:")?`${modal.split(":")[1]} 학생에게 새 임시 비밀번호를 발급했습니다`:"입력 내용을 검증해 체험 목록에 반영했습니다");
    }}/>}</div>
}

function CardHead({title,action,onClick}:{title:string;action?:string;onClick?:()=>void}){return <div className="staff-card-head"><h2>{title}</h2>{action&&<button onClick={onClick}>{action}</button>}</div>}
function FilterRow({teacher,week,setWeek}:{teacher:string;week:string;setWeek:(v:string)=>void}){return <div className="filter-row"><Field label="담당 선생님"><select defaultValue={teacher}><option>{teacher}</option></select></Field><Field label="기준 주"><input type="date" value={week} onChange={e=>setWeek(e.target.value)}/></Field><Field label="반"><select><option>전체 반</option></select></Field><button><Search/>조회</button></div>}
function Field({label,children}:{label:string;children:React.ReactNode}){return <label className="staff-field"><span>{label}</span>{children}</label>}
function modalTitle(key:string){if(key.startsWith("reset:"))return `${key.split(":")[1]} 학생 비밀번호 초기화`;if(key.startsWith("bookEdit:"))return "교재 정보 수정";return ({gradeUpload:"채점결과 파일 검증",rosterUpload:"학생 명단 업로드 미리보기",transfer:"오답 계정 이전",studentEdit:"학생 정보 수정",bookAdd:"새 교재 등록",examAdd:"학교 기출 등록",examEdit:"학교 기출 수정",noticeAdd:"새 공지 작성",noticeEdit:"공지 수정",recordEdit:"오답 기록 수정",restore:"회원목록 일괄 복구"} as Record<string,string>)[key]||"정보 수정"}
function DemoModal({title,onClose,onSave}:{title:string;onClose:()=>void;onSave:()=>void}){return <div className="modal-backdrop" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}><section className="demo-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><button className="modal-close" onClick={onClose} aria-label="닫기"><X/></button><span className="pill">체험 입력</span><h2 id="modal-title">{title}</h2><p>실제 데이터에는 반영되지 않습니다. 운영 연결 전 권한·입력값·중복 여부를 서버에서 다시 검사합니다.</p><Field label="대상 또는 이름"><input placeholder="이름을 입력해 주세요"/></Field><Field label="변경 내용"><input placeholder="변경할 내용을 입력해 주세요"/></Field><label className="confirm"><input type="checkbox"/>변경 내용을 확인했습니다.</label><div className="modal-actions"><button onClick={onClose}>취소</button><button className="staff-primary" onClick={onSave}>검증 후 적용</button></div></section></div>}
