"""AiChat Pro v50 — Map Engine: Pathfinding, travel, territory."""
import math
from collections import deque
from core.storage import get_conn

def _build_adj(wid):
    conn=get_conn(); locs=conn.execute("SELECT id,x,y FROM world_locations WHERE world_id=?",(wid,)).fetchall(); conn.close()
    adj={l["id"]:[] for l in locs}
    for i,a in enumerate(locs):
        for b in locs[i+1:]:
            if math.sqrt((a["x"]-b["x"])**2+(a["y"]-b["y"])**2)<=5:
                adj[a["id"]].append(b["id"]); adj[b["id"]].append(a["id"])
    for l in locs:
        if not adj[l["id"]]:
            best=min((o for o in locs if o["id"]!=l["id"]),key=lambda o:math.sqrt((l["x"]-o["x"])**2+(l["y"]-o["y"])**2),default=None)
            if best: adj[l["id"]].append(best["id"]); adj[best["id"]].append(l["id"])
    return adj

def find_path(wid, start, end):
    adj=_build_adj(wid)
    if start not in adj or end not in adj: return []
    visited={start}; q=deque([(start,[start])])
    while q:
        cur,path=q.popleft()
        if cur==end: return path
        for n in adj.get(cur,[]):
            if n not in visited: visited.add(n); q.append((n,path+[n]))
    return []

def travel_cost(wid, start, end):
    path=find_path(wid,start,end)
    if not path: return {"path":[],"cost":0,"blocked":True,"reason":"No path"}
    conn=get_conn(); w=conn.execute("SELECT weather FROM worlds WHERE id=?",(wid,)).fetchone(); conn.close()
    weather=w["weather"] if w else "clear"
    if weather in {"storm","blizzard"}: return {"path":path,"cost":len(path)-1,"blocked":True,"reason":f"Blocked by {weather}"}
    conn=get_conn(); names=[conn.execute("SELECT name FROM world_locations WHERE id=?",(lid,)).fetchone() for lid in path]; conn.close()
    return {"path":path,"names":[n["name"] if n else f"Loc {path[i]}" for i,n in enumerate(names)],"cost":len(path)-1,"blocked":False}

def get_faction_territories(wid):
    conn=get_conn(); rows=conn.execute("SELECT name,owner FROM world_locations WHERE world_id=? AND owner IS NOT NULL AND owner!=''",(wid,)).fetchall(); conn.close()
    t={}
    for r in rows: t.setdefault(r["owner"],[]).append(r["name"])
    return t
