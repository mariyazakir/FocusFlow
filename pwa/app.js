(() => {
  const STORAGE_KEY = "focusflow.pwa.tasks.v1";
  const THEME_KEY = "focusflow.pwa.theme.v1";
  const CONSENT_KEY = "focusflow.pwa.legal-consent.v1";
  const LEGAL_VERSION = "2026-10-12-v2";
  const CATEGORIES = ["MCA", "Side Income", "BUD", "Personal"];
  const PRIORITIES = ["High", "Medium", "Low"];
  const STATUSES = ["To do", "In progress", "Done"];
  const STATUS_COLOR = {"To do":"#7084ed","In progress":"#e7a744","Done":"#32a889"};
  const PRIORITY_COLOR = {High:"#e56776",Medium:"#e7a744",Low:"#32a889"};
  const appState = { page:"overview", tasks:[], month:firstOfMonth(new Date()), selected:dateKey(new Date()), query:"", category:"All categories", status:"All statuses" };
  const view = document.querySelector("#view");
  const taskDialog = document.querySelector("#taskDialog");
  const form = document.querySelector("#taskForm");
  let toastTimer;

  function loadTasks(){try{const parsed=JSON.parse(localStorage.getItem(STORAGE_KEY)||"[]");return Array.isArray(parsed)?parsed:[]}catch{return []}}
  function saveTasks(){localStorage.setItem(STORAGE_KEY,JSON.stringify(appState.tasks));}
  function dateKey(d){const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,"0"),day=String(d.getDate()).padStart(2,"0");return `${y}-${m}-${day}`}
  function parseDate(value){if(!value)return null;const [y,m,d]=value.split("-").map(Number);return new Date(y,m-1,d)}
  function firstOfMonth(d){return new Date(d.getFullYear(),d.getMonth(),1)}
  function addDays(d,n){const next=new Date(d);next.setDate(next.getDate()+n);return next}
  function escapeHtml(value=""){return String(value).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
  function labelDate(value, options={month:"short",day:"numeric"}){const d=parseDate(value);return d?new Intl.DateTimeFormat(undefined,options).format(d):"No deadline"}
  function showToast(message){const el=document.querySelector("#toast");el.textContent=message;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),2300)}
  function activeTasks(){return appState.tasks.filter(t=>t.status!=="Done")}
  function taskMeta(task){return `${escapeHtml(task.category)} · ${escapeHtml(task.priority)} · ${labelDate(task.due_date)} · ${Number(task.estimated_minutes)||30} min`}

  function render(){
    document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.page===appState.page));
    if(appState.page==="overview")renderOverview();
    else if(appState.page==="tasks")renderTasks();
    else if(appState.page==="calendar")renderCalendar();
    else if(appState.page==="planner")renderPlanner();
    else renderBoard();
  }

  function reminderHtml(){
    const today=dateKey(new Date());
    const overdue=activeTasks().filter(t=>t.due_date&&t.due_date<today);
    const due=activeTasks().filter(t=>t.due_date===today);
    if(overdue.length)return `<div class="alert">⏰ ${overdue.length} unfinished task${overdue.length===1?" is":"s are"} past due. Review the carryovers in Calendar.</div>`;
    if(due.length)return `<div class="alert">⏰ ${due.length} task${due.length===1?" is":"s are"} due today. Take them one at a time.</div>`;
    return "";
  }

  function renderOverview(){
    const tasks=appState.tasks,active=activeTasks(),done=tasks.filter(t=>t.status==="Done"),today=dateKey(new Date());
    const due=active.filter(t=>t.due_date===today),overdue=active.filter(t=>t.due_date&&t.due_date<today);
    const upcoming=[...active].filter(t=>t.due_date).sort((a,b)=>a.due_date.localeCompare(b.due_date)).slice(0,5);
    const ratio=tasks.length?Math.round(done.length/tasks.length*100):0;
    const counts=CATEGORIES.map(category=>[category,active.filter(t=>t.category===category).length]).filter(([,count])=>count);
    const catTotal=counts.reduce((sum,item)=>sum+item[1],0)||1;
    let offset=0;const palette=["var(--accent)","var(--mint)","#e7a744","#e56776"];
    const segments=counts.map(([name,count],index)=>{const start=offset;offset+=count/catTotal*100;return `${palette[index%palette.length]} ${start}% ${offset}%`}).join(", ");
    view.innerHTML=`<div class="hero"><div class="eyebrow">${new Intl.DateTimeFormat(undefined,{weekday:"long",month:"long",day:"numeric"}).format(new Date()).toUpperCase()}</div><h1>${greeting()}, let’s find your focus.</h1><p>A clear plan makes a lighter day. You’ve got this.</p></div>
      ${reminderHtml()}<div class="metric-grid">${metric("Active tasks",active.length,"Ready when you are","◉")}${metric("Due today",due.length,"One step at a time","◷")}${metric("Completed",done.length,"Things you’ve moved forward","✓")}${metric("Overdue",overdue.length,"Review and reschedule","↗")}</div>
      <div class="content-grid"><section class="panel"><h2>Your next steps</h2><p class="section-sub">The nearest deadlines, all in one place.</p>${upcoming.length?upcoming.map(t=>`<div class="task-preview"><b>${escapeHtml(t.title)}</b><small>${taskMeta(t)}</small></div>`).join(""):`<div class="empty-state">Your next steps will appear here. Add a task to get started.</div>`}</section>
      <section class="panel"><h2>Where your time goes</h2><p class="section-sub">Active tasks by category</p>${counts.length?`<div style="width:150px;height:150px;margin:23px auto;border-radius:50%;background:conic-gradient(${segments})"><div style="width:94px;height:94px;background:var(--panel);border-radius:50%;position:relative;top:28px;left:28px"></div></div><div class="board-meta">${counts.map(([name,count],i)=>`<span class="badge" style="color:${palette[i%palette.length]}">● ${escapeHtml(name)} ${count}</span>`).join("")}</div>`:`<div class="empty-state">Add tasks to see your category mix.</div>`}</section></div>
      <section class="panel" style="margin-top:20px"><h2>Progress at a glance</h2><p class="section-sub">${done.length} of ${tasks.length} tasks completed</p><div class="progress-track" style="margin-top:14px"><div class="progress-fill" style="width:${ratio}%"></div></div></section>`;
  }
  function metric(name,value,foot,icon){return `<div class="metric"><div class="metric-label">${icon} &nbsp;${name}</div><div class="metric-value">${value}</div><div class="metric-foot">${foot}</div></div>`}
  function greeting(){const h=new Date().getHours();return h<12?"Good morning":h<18?"Good afternoon":"Good evening"}

  function renderTasks(){
    const list=appState.tasks.filter(t=>t.title.toLowerCase().includes(appState.query.toLowerCase())||(t.description||"").toLowerCase().includes(appState.query.toLowerCase())).filter(t=>appState.category==="All categories"||t.category===appState.category).filter(t=>appState.status==="All statuses"||t.status===appState.status).sort(sortTasks);
    view.innerHTML=`<div class="section-head"><div><h1 class="page-title">My tasks</h1><p class="section-sub">Everything you’re working on, in one calm place.</p></div><button class="button primary" id="addTaskTop">＋ Add task</button></div>
      <div class="filter-row"><input id="searchTasks" type="search" placeholder="Search by name or notes…" value="${escapeHtml(appState.query)}"><select id="filterCategory"><option>All categories</option>${CATEGORIES.map(c=>`<option ${appState.category===c?"selected":""}>${c}</option>`).join("")}</select><select id="filterStatus"><option>All statuses</option>${STATUSES.map(s=>`<option ${appState.status===s?"selected":""}>${s}</option>`).join("")}</select></div>
      <div class="task-list-tools"><button id="printTasks" class="button secondary">▤ Print task list (${list.length})</button><small>Print includes the tasks that match your filters.</small></div>
      ${list.length?list.map(renderTaskRow).join(""):`<div class="empty-state">No matching tasks. Try another filter or add something new.</div>`}`;
    document.querySelector("#addTaskTop").onclick=()=>openTaskDialog();
    document.querySelector("#searchTasks").oninput=e=>{appState.query=e.target.value;renderTasksKeepFocus(e.target.selectionStart)};
    document.querySelector("#filterCategory").onchange=e=>{appState.category=e.target.value;renderTasks()};
    document.querySelector("#filterStatus").onchange=e=>{appState.status=e.target.value;renderTasks()};
    document.querySelector("#printTasks").onclick=()=>printTaskList(list);
    document.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>openTaskDialog(findTask(b.dataset.edit)));
    document.querySelectorAll("[data-delete]").forEach(b=>b.onclick=()=>deleteTask(b.dataset.delete));
    document.querySelectorAll("[data-status]").forEach(s=>s.onchange=()=>setStatus(s.dataset.status,s.value));
  }
  function renderTasksKeepFocus(position){renderTasks();const input=document.querySelector("#searchTasks");input.focus();input.setSelectionRange(position,position)}
  function renderTaskRow(task){return `<article class="task-row"><div class="task-main"><h3>${escapeHtml(task.title)}</h3><p>${taskMeta(task)}</p>${task.description?`<p style="margin-top:6px">${escapeHtml(task.description)}</p>`:""}</div><select class="task-status" aria-label="Status for ${escapeHtml(task.title)}" data-status="${task.id}">${STATUSES.map(s=>`<option ${task.status===s?"selected":""}>${s}</option>`).join("")}</select><div class="task-actions"><button class="button secondary" data-edit="${task.id}">✎ Edit</button><button class="button secondary danger" data-delete="${task.id}">Delete</button></div></article>`}
  function sortTasks(a,b){const order={High:0,Medium:1,Low:2};return (a.due_date||"9999").localeCompare(b.due_date||"9999")||(order[a.priority]-order[b.priority])}

  function renderCalendar(){
    const month=appState.month,today=dateKey(new Date()),start=new Date(month.getFullYear(),month.getMonth(),1),end=new Date(month.getFullYear(),month.getMonth()+1,0);
    const gridStart=addDays(start,-((start.getDay()+6)%7)),gridEnd=addDays(end,6-((end.getDay()+6)%7));
    const days=[];for(let d=new Date(gridStart);d<=gridEnd;d=addDays(d,1))days.push(new Date(d));
    const weekdays=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
    const carry=activeTasks().filter(t=>t.due_date&&t.due_date<today).sort((a,b)=>a.due_date.localeCompare(b.due_date));
    view.innerHTML=`<div class="section-head"><div><h1 class="page-title">Calendar</h1><p class="section-sub">Choose any day to add or review its tasks.</p></div></div>
      <div class="calendar-top"><button class="button secondary" id="prevMonth">← Previous</button><h2>${new Intl.DateTimeFormat(undefined,{month:"long",year:"numeric"}).format(month)}</h2><button class="button secondary" id="nextMonth">Next →</button></div>
      <div class="calendar-grid">${weekdays.map(d=>`<div class="weekday">${d}</div>`).join("")}${days.map(d=>calendarDay(d,month,today)).join("")}</div>
      <section class="panel calendar-selection"><h3>${labelDate(appState.selected,{weekday:"long",month:"long",day:"numeric",year:"numeric"})}</h3><div id="selectedDayTasks"></div><button class="button primary" id="addSelectedDay">＋ Add task on this day</button></section>
      <section class="panel" style="margin-top:15px"><div class="section-head" style="margin:0 0 9px"><div><h2>Past-due carryovers</h2><p class="section-sub">Old tasks stay on their original date until you reschedule them.</p></div></div><div class="carry-list">${carry.length?carry.map(t=>`<div class="carry-item"><span><b>${escapeHtml(t.title)}</b><small class="muted"> · due ${labelDate(t.due_date)} · ${t.estimated_minutes} min</small></span><button class="button secondary" data-carry="${t.id}">Move to today</button></div>`).join(""):`<span class="muted">No unfinished past-due tasks.</span>`}</div></section>`;
    document.querySelectorAll("[data-calendar-date]").forEach(b=>b.onclick=()=>{appState.selected=b.dataset.calendarDate;renderCalendar()});
    document.querySelector("#prevMonth").onclick=()=>{appState.month=new Date(month.getFullYear(),month.getMonth()-1,1);appState.selected=dateKey(appState.month);renderCalendar()};
    document.querySelector("#nextMonth").onclick=()=>{appState.month=new Date(month.getFullYear(),month.getMonth()+1,1);appState.selected=dateKey(appState.month);renderCalendar()};
    document.querySelector("#addSelectedDay").onclick=()=>openTaskDialog(null,appState.selected);
    document.querySelectorAll("[data-carry]").forEach(b=>b.onclick=()=>{const task=findTask(b.dataset.carry);task.due_date=today;saveTasks();renderCalendar();showToast("Task moved to today.")});
    const selectedTasks=appState.tasks.filter(t=>t.due_date===appState.selected).sort(sortTasks);
    document.querySelector("#selectedDayTasks").innerHTML=selectedTasks.length?selectedTasks.map(t=>`<div class="task-preview"><b>${escapeHtml(t.title)}</b><small>${escapeHtml(t.status)} · ${t.estimated_minutes} min · ${escapeHtml(t.priority)}</small></div>`).join(""):`<p class="muted">No tasks due on this day yet.</p>`;
  }
  function calendarDay(day,month,today){const key=dateKey(day),items=appState.tasks.filter(t=>t.due_date===key).sort(sortTasks);return `<div class="day-cell ${day.getMonth()!==month.getMonth()?"outside":""} ${key===today?"today":""}"><button class="day-number ${key===appState.selected?"selected":""}" data-calendar-date="${key}" aria-label="Select ${new Intl.DateTimeFormat(undefined,{month:"long",day:"numeric"}).format(day)}">${day.getDate()}</button>${items.slice(0,3).map(t=>`<div class="day-event ${t.status!=="Done"&&key<today?"overdue":""}" title="${escapeHtml(t.title)}">${t.status==="Done"?"✓":"•"} ${escapeHtml(t.title)}</div>`).join("")}${items.length>3?`<div class="day-event">+${items.length-3} more</div>`:""}</div>`}

  function renderPlanner(){
    const today=dateKey(new Date());
    view.innerHTML=`<div class="section-head"><div><h1 class="page-title">Plan your day</h1><p class="section-sub">A free offline plan ranked by priority and deadline.</p></div></div>${reminderHtml()}
      <div class="planner-controls"><label>Plan date<input type="date" id="planDate" value="${today}"></label><label>Available focus time (min)<input type="number" id="focusCapacity" min="30" max="720" step="15" value="240"></label><label>Start at<input type="time" id="startAt" value="09:00"></label><label>Break (min)<input type="number" id="breakLength" min="0" max="30" step="5" value="10"></label></div><button class="button primary" id="buildPlan">↗ Build my schedule</button><div id="schedule" style="margin-top:18px"></div>
      <div class="section-head"><div><h2>Quick task breakdowns</h2><p class="section-sub">Editable local starter checklists. Nothing is sent to an AI service.</p></div></div><div id="breakdowns"></div>`;
    document.querySelector("#buildPlan").onclick=()=>drawSchedule();
    document.querySelectorAll("[data-planner-edit]").forEach(b=>b.onclick=()=>openTaskDialog(findTask(b.dataset.plannerEdit)));
    drawSchedule();drawBreakdowns();
  }
  function drawSchedule(){
    const date=document.querySelector("#planDate").value,capacity=Math.max(0,Number(document.querySelector("#focusCapacity").value)||0),breakMins=Number(document.querySelector("#breakLength").value)||0;
    const [sh,sm]=document.querySelector("#startAt").value.split(":").map(Number);let cursor=sh*60+sm,remaining=capacity;
    const list=activeTasks().sort((a,b)=>PRIORITIES.indexOf(a.priority)-PRIORITIES.indexOf(b.priority)||(a.due_date||"9999").localeCompare(b.due_date||"9999"));
    const plan=[];for(const task of list){const duration=Number(task.estimated_minutes)||30;if(duration>remaining)continue;plan.push({task,start:cursor,end:cursor+duration});cursor+=duration+breakMins;remaining-=duration}
    const used=capacity-remaining;
    document.querySelector("#schedule").innerHTML=`<h2>Suggested schedule</h2><p class="muted">${used} of ${capacity} focus minutes planned${date?` · ${labelDate(date,{weekday:"long",month:"long",day:"numeric"})}`:""}</p>${plan.length?`<div class="schedule-list">${plan.map(item=>`<article class="schedule-item"><span class="schedule-time">${clock(item.start)} – ${clock(item.end)}</span><span><b>${escapeHtml(item.task.title)}</b><br><small>${item.task.estimated_minutes} min · ${escapeHtml(item.task.category)} · ${escapeHtml(item.task.priority)}</small></span><button class="button secondary" data-planner-edit="${item.task.id}">Edit</button></article>`).join("")}</div>`:`<div class="empty-state">No tasks fit the selected time budget.</div>`}`;
    document.querySelectorAll("[data-planner-edit]").forEach(b=>b.onclick=()=>openTaskDialog(findTask(b.dataset.plannerEdit)));
  }
  function clock(minutes){const h=Math.floor(minutes/60)%24,m=minutes%60;const suffix=h<12?"AM":"PM",hour=h%12||12;return `${hour}:${String(m).padStart(2,"0")} ${suffix}`}
  function drawBreakdowns(){
    const tasks=[...activeTasks()].sort(sortTasks).slice(0,8),container=document.querySelector("#breakdowns");
    container.innerHTML=tasks.length?tasks.map(task=>{task.steps ||= makeSteps(task);return `<details class="breakdown"><summary>${escapeHtml(task.title)} <span class="muted">· ${task.estimated_minutes} min</span></summary><div style="display:flex;justify-content:flex-end;margin-top:9px"><button class="button secondary" data-edit="${task.id}">✎ Edit task</button></div><div class="checklist">${task.steps.map((step,i)=>`<label><input type="checkbox" data-step-task="${task.id}" data-step-index="${i}" ${step.done?"checked":""}>${escapeHtml(step.text)}</label>`).join("")}</div></details>`}).join(""):`<div class="empty-state">Add a task to get a starter checklist.</div>`;
    container.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>openTaskDialog(findTask(b.dataset.edit)));
    container.querySelectorAll("[data-step-task]").forEach(input=>input.onchange=()=>{const task=findTask(input.dataset.stepTask);task.steps[Number(input.dataset.stepIndex)].done=input.checked;saveTasks()});
  }
  function makeSteps(task){const templates={MCA:["Read the prompt and note the requirements","Gather class notes and references","Complete the work in focused sections","Review against the rubric and submit"],"Side Income":["Define the outcome and who it is for","Prepare the materials and tools","Complete the highest-value part first","Check the result and plan the next action"],BUD:["Write down the smallest useful outcome","Sketch the approach","Build and check one small piece at a time","Review what works and note the next improvement"],Personal:["Decide what finished looks like","Gather what you need","Work through a few small steps","Check it off and prepare what comes next"]};return templates[task.category].map(text=>({text,done:false}))}

  function renderBoard(){
    view.innerHTML=`<div class="section-head"><div><h1 class="page-title">Your board</h1><p class="section-sub">Open a task card to see its notes and focus time.</p></div><button id="addBoardTask" class="button primary">＋ Add task</button></div>
      <div class="board-grid">${STATUSES.map(status=>{const tasks=appState.tasks.filter(t=>t.status===status).sort(sortTasks);return `<section class="board-column"><h2><span style="color:${STATUS_COLOR[status]}">${status}</span><span class="badge">${tasks.length}</span></h2>${tasks.length?tasks.map(boardCard).join(""):`<p class="muted">Nothing here yet.</p>`}</section>`}).join("")}</div>`;
    document.querySelector("#addBoardTask").onclick=()=>openTaskDialog();
    document.querySelectorAll("[data-status]").forEach(select=>select.onchange=()=>setStatus(select.dataset.status,select.value));
  }
  function boardCard(task){return `<article class="board-card" style="border-left-color:${PRIORITY_COLOR[task.priority]}"><h3>${escapeHtml(task.title)}</h3><div class="board-meta"><span class="badge" style="color:${STATUS_COLOR[task.status]}">${escapeHtml(task.category)}</span><span class="badge" style="color:${PRIORITY_COLOR[task.priority]}">${escapeHtml(task.priority)}</span><span class="badge">${Number(task.estimated_minutes)||30} min</span>${task.due_date?`<span class="badge">${labelDate(task.due_date)}</span>`:""}</div><label style="display:flex;align-items:center;gap:8px;margin-top:10px;color:var(--muted);font-size:11px">Move to <select data-status="${task.id}" aria-label="Change status for ${escapeHtml(task.title)}" style="padding:5px 7px">${STATUSES.map(s=>`<option ${task.status===s?"selected":""}>${s}</option>`).join("")}</select></label><details><summary>Notes &amp; focus details</summary><div class="details-body"><b>Focus time:</b> ${Number(task.estimated_minutes)||30} minutes<br><b>Deadline:</b> ${labelDate(task.due_date)}<br><b>Notes:</b><br>${escapeHtml(task.description||"No notes for this task.")}</div></details></article>`}

  function openTaskDialog(task=null,dueDate=null){
    form.reset();const data=task||{id:"",title:"",description:"",category:"MCA",priority:"Medium",due_date:dueDate||"",estimated_minutes:45,status:"To do",recurring:"Never"};
    form.elements.id.value=data.id||"";form.elements.title.value=data.title||"";form.elements.description.value=data.description||"";form.elements.category.value=data.category||"MCA";form.elements.priority.value=data.priority||"Medium";form.elements.due_date.value=dueDate||data.due_date||"";form.elements.estimated_minutes.value=data.estimated_minutes||45;form.elements.status.value=data.status||"To do";form.elements.recurring.value=data.recurring||"Never";
    document.querySelector("#formTitle").textContent=task?"Edit task":"Add a task";document.querySelector("#formEyebrow").textContent=task?"UPDATE DETAILS":"NEW TASK";taskDialog.showModal();form.elements.title.focus();
  }
  function saveTask(event){event.preventDefault();const data=Object.fromEntries(new FormData(form));data.title=data.title.trim();if(!data.title)return;data.estimated_minutes=Math.min(1440,Math.max(5,Number(data.estimated_minutes)||45));
    if(data.id){const old=findTask(data.id);Object.assign(old,data);if(old.status!=="Done"&&data.status==="Done")createNextOccurrence(old)}else{data.id=crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;data.created_at=new Date().toISOString();data.steps=[];appState.tasks.push(data)}
    const editing=Boolean(form.elements.id.value);saveTasks();taskDialog.close();render();showToast(editing?"Task saved.":"Task added.");
  }
  function createNextOccurrence(task){if(!task.recurring||task.recurring==="Never")return;const due=parseDate(task.due_date)||new Date();if(task.recurring==="Daily")due.setDate(due.getDate()+1);else if(task.recurring==="Weekly")due.setDate(due.getDate()+7);else{const day=due.getDate();due.setDate(1);due.setMonth(due.getMonth()+1);due.setDate(Math.min(day,new Date(due.getFullYear(),due.getMonth()+1,0).getDate()))}appState.tasks.push({...task,id:crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`,status:"To do",due_date:dateKey(due),created_at:new Date().toISOString(),steps:[]})}
  function findTask(id){return appState.tasks.find(t=>String(t.id)===String(id))}
  function deleteTask(id){if(!confirm("Delete this task?"))return;appState.tasks=appState.tasks.filter(t=>String(t.id)!==String(id));saveTasks();render();showToast("Task deleted.")}
  function setStatus(id,status){const task=findTask(id),old=task.status;task.status=status;if(old!=="Done"&&status==="Done")createNextOccurrence(task);saveTasks();render();showToast(status==="Done"?"Nice work — task completed.":"Task status updated.")}
  function printTaskList(tasks){const printable=tasks.map(t=>`<article class="print-task"><h2>□ &nbsp;${escapeHtml(t.title)} <span style="float:right;font-size:11px;font-weight:400">${escapeHtml(t.status)}</span></h2><p class="print-meta">${escapeHtml(t.category)} · ${escapeHtml(t.priority)} · ${labelDate(t.due_date)} · ${Number(t.estimated_minutes)||30} min</p>${t.description?`<p class="print-notes">${escapeHtml(t.description)}</p>`:""}</article>`).join("");document.querySelector("#printArea").innerHTML=`<h1>FocusFlow task list</h1><p class="print-sub">Printed ${new Intl.DateTimeFormat().format(new Date())} · ${tasks.length} task${tasks.length===1?"":"s"}</p>${printable||"<p>No tasks match the current filters.</p>"}`;window.print()}

  function renderPlannerAfterEdit(){saveTasks();render();}

  document.querySelectorAll(".nav-item").forEach(button=>button.addEventListener("click",()=>{appState.page=button.dataset.page;render()}));
  document.querySelectorAll(".brand").forEach(brand=>brand.addEventListener("click",event=>{event.preventDefault();appState.page="overview";render()}));
  document.querySelector("#sidebarAdd").onclick=()=>openTaskDialog();document.querySelector("#mobileAdd").onclick=()=>openTaskDialog();
  document.querySelector("#closeDialog").onclick=()=>taskDialog.close();document.querySelector("#cancelDialog").onclick=()=>taskDialog.close();form.addEventListener("submit",saveTask);
  document.querySelector("#themeSelect").value=localStorage.getItem(THEME_KEY)||"dark";document.documentElement.dataset.theme=document.querySelector("#themeSelect").value;
  document.querySelector("#themeSelect").onchange=e=>{document.documentElement.dataset.theme=e.target.value;localStorage.setItem(THEME_KEY,e.target.value)};
  document.querySelector("#mobileTheme").onclick=()=>{const next=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=next;document.querySelector("#themeSelect").value=next;localStorage.setItem(THEME_KEY,next)};
  document.querySelector("#exportButton").onclick=()=>{const blob=new Blob([JSON.stringify({app:"FocusFlow",version:1,tasks:appState.tasks},null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download=`focusflow-backup-${dateKey(new Date())}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);showToast("Backup downloaded.")};
  document.querySelector("#importInput").onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{const data=JSON.parse(await file.text()),tasks=Array.isArray(data)?data:data.tasks;if(!Array.isArray(tasks))throw new Error("This file does not contain a FocusFlow task list.");if(!confirm(`Replace this browser's ${appState.tasks.length} tasks with ${tasks.length} imported tasks?`))return;appState.tasks=tasks.map((t,i)=>({...t,id:t.id||`import-${Date.now()}-${i}`,estimated_minutes:Number(t.estimated_minutes)||30,status:STATUSES.includes(t.status)?t.status:"To do",recurring:t.recurring||"Never",steps:Array.isArray(t.steps)?t.steps:[]}));saveTasks();render();showToast("Backup imported.")}catch(error){alert(error.message||"Could not read this backup.")}finally{e.target.value=""}};
  taskDialog.addEventListener("click",e=>{if(e.target===taskDialog)taskDialog.close()});
  window.addEventListener("beforeinstallprompt",event=>{event.preventDefault();window.installPrompt=event;["#installButton","#installMobile"].forEach(selector=>{const button=document.querySelector(selector);if(button)button.hidden=false})});
  if("serviceWorker" in navigator && (location.protocol==="https:"||location.hostname==="localhost"))navigator.serviceWorker.register("/sw.js").catch(()=>{});
  ["#installButton","#installMobile"].forEach(selector=>{const button=document.querySelector(selector);if(button)button.onclick=async()=>{if(window.installPrompt){window.installPrompt.prompt();await window.installPrompt.userChoice;window.installPrompt=null;["#installButton","#installMobile"].forEach(id=>{const el=document.querySelector(id);if(el)el.hidden=true})}else showToast("Use your browser menu and choose Add to Home Screen.")}});
  const consentDialog=document.querySelector("#consentDialog"),termsConsent=document.querySelector("#termsConsent"),privacyConsent=document.querySelector("#privacyConsent"),adultConsent=document.querySelector("#adultConsent"),acceptConsent=document.querySelector("#acceptConsent");
  const refreshConsentButton=()=>{acceptConsent.disabled=!window.FocusFlowLegal.canContinue(termsConsent.checked,privacyConsent.checked,adultConsent.checked)};
  [termsConsent,privacyConsent,adultConsent].forEach(input=>input.addEventListener("change",refreshConsentButton));
  acceptConsent.addEventListener("click",()=>{if(acceptConsent.disabled)return;localStorage.setItem(CONSENT_KEY,JSON.stringify({version:LEGAL_VERSION,acceptedAt:new Date().toISOString(),adultAttested:true}));appState.tasks=loadTasks();consentDialog.close();render()});
  consentDialog.addEventListener("cancel",event=>event.preventDefault());
  let previousConsent=null;try{previousConsent=JSON.parse(localStorage.getItem(CONSENT_KEY)||"null")}catch{}
  if(previousConsent?.version!==LEGAL_VERSION||previousConsent?.adultAttested!==true)consentDialog.showModal();
  else{appState.tasks=loadTasks();render()}
})();
