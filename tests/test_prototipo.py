import json, os, time
from playwright.sync_api import sync_playwright
import os
URL=os.environ.get('URL','http://127.0.0.1:8765/index.html')
R={}
size=os.path.getsize('index.html')
R['size_kb']=round(size/1024,1)
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,locale='es-CO')
    pg=ctx.new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller || true"); pg.evaluate("navigator.serviceWorker.ready.then(()=>1)"); pg.reload(); pg.wait_for_timeout(800)
    pg.screenshot(path='docs/capturas/01_login.png')
    # PF-01
    pg.fill('#lu','est'); pg.fill('#lp','0000'); pg.click('text=Entrar')
    R['PF01_invalid']='Usuario o contraseña incorrectos' in pg.inner_text('#app')
    pg.fill('#lu','est'); pg.fill('#lp','1234'); pg.click('text=Entrar')
    R['PF01_valid']='Hola, Estudiante Demo' in pg.inner_text('#app')
    # PF-02 nav by role
    navs={}
    navs['estudiante']=pg.inner_text('#nav')
    pg.screenshot(path='docs/capturas/02_home_est.png')
    # course
    pg.click('text=Abrir >> nth=0'); pg.screenshot(path='docs/capturas/03_course.png')
    # PF-05 download
    pg.click('text=Abrir >> nth=0'); pg.click('text=Descargar para sin conexión')
    R['PF05_download_marked']='Descargado' in pg.inner_text('#app')
    ctx.set_offline(True)
    pg.click('text=Marcar como completado')
    R['PF05_offline_navigation']='Actividad completada' in pg.inner_text('#app') and pg.inner_text('#net')=='Sin conexión'
    pg.screenshot(path='docs/capturas/04_resource_offline.png')
    ctx.set_offline(False)
    # reload offline test (limitation)
    ctx.set_offline(True)
    try:
        pg.reload(timeout=4000); R['reload_offline']='carga sin red con el service worker: '+str(pg.locator('#lu').count()==1)
    except Exception as e:
        R['reload_offline']='falla al recargar sin red (no hay service worker)'
    ctx.set_offline(False); pg.goto(URL); pg.fill('#lu','est'); pg.fill('#lp','1234'); pg.click('text=Entrar')
    R['persistence_after_reload']=True if 'Avance: 17' in pg.inner_text('#app') else pg.inner_text('#app')[:200]
    # PF-06 quiz
    pg.click('text=Abrir >> nth=0'); pg.click('text=Abrir >> nth=2')
    for i,j in enumerate([0,1,0]): pg.check(f'input[name=q{i}][value="{j}"]')
    pg.click('text=Enviar respuestas'); R['PF06_quiz']=pg.inner_text('#qr')
    pg.screenshot(path='docs/capturas/05_quiz.png')
    # PF-07 task
    pg.click('text=← Volver al curso'); pg.click('text=Abrir >> nth=3')
    pg.click('text=Entregar tarea'); R['PF07_empty_blocked']='Escribe tu respuesta' in pg.inner_text('#app')
    pg.fill('#tx','Mi análisis del caso'); pg.click('text=Entregar tarea'); R['PF07_submit']='Entrega recibida' in pg.inner_text('#app')
    # PF-09 forum
    pg.click('text=← Volver al curso'); pg.click('text=Abrir >> nth=4'); pg.fill('#fp','Aprendí fracciones'); pg.click('text=Publicar')
    R['PF09_forum']='Aprendí fracciones' in pg.inner_text('#app')
    # XSS escape
    pg.fill('#fp','<img src=x onerror=alert(1)>'); pg.click('text=Publicar'); R['XSS_escaped']='<img src=x' in pg.inner_text('#app') and pg.locator('#app img').count()==0
    pg.screenshot(path='docs/capturas/06_forum.png')
    # grades
    pg.click('nav >> text=Notas'); R['PF08_grades_view']=pg.inner_text('#app')[:160].replace('\n',' | ')
    pg.screenshot(path='docs/capturas/07_grades.png')
    # SUS calc
    pg.click('nav >> text=Evaluar app')
    for i in range(10): pg.select_option(f'#s{i}', '5' if i%2==0 else '1')
    pg.click('text=Calcular puntaje'); R['SUS_best']=pg.inner_text('#sr')
    for i in range(10): pg.select_option(f'#s{i}', '3')
    pg.click('text=Calcular puntaje'); R['SUS_neutral']=pg.inner_text('#sr')
    pg.screenshot(path='docs/capturas/08_sus.png')
    # PS-01 role restrictions
    pg.click('nav >> text=Salir')
    pg.fill('#lu','dir'); pg.fill('#lp','1234'); pg.click('text=Entrar')
    R['PS01_dir_nav']=pg.inner_text('#nav').replace('\n',' ')
    R['PS01_dir_sees_courses']='Abrir' in pg.inner_text('#app')
    pg.click('nav >> text=Informes'); pg.screenshot(path='docs/capturas/09_reporte.png'); R['PF10_report']='Informe de participación' in pg.inner_text('#app')
    pg.click('nav >> text=Salir')
    pg.fill('#lu','doc'); pg.fill('#lp','1234'); pg.click('text=Entrar'); navs['docente']=pg.inner_text('#nav').replace('\n',' ')
    pg.fill('#av','Mañana hay actividad'); pg.click('button:has-text("Publicar")'); R['aviso_docente']='Aviso publicado' in pg.inner_text('#app')
    pg.screenshot(path='docs/capturas/10_docente.png')
    pg.click('nav >> text=Salir')
    pg.fill('#lu','adm'); pg.fill('#lp','1234'); pg.click('text=Entrar'); navs['administrador']=pg.inner_text('#nav').replace('\n',' ')
    pg.click('nav >> text=Admin'); pg.click('text=Crear copia de respaldo'); R['PS02_backup']='Copia de respaldo creada' in pg.inner_text('#app')
    pg.click('text=Restaurar última copia'); R['PS02_restore']='Copia restaurada' in pg.inner_text('#app')
    pg.screenshot(path='docs/capturas/11_admin.png')
    R['navs']=navs
    # PA-01 basic accessibility
    pg.click('nav >> text=Salir')
    small=pg.evaluate("""()=>[...document.querySelectorAll('button,input,select,textarea')].filter(e=>e.offsetParent&&e.getBoundingClientRect().height<40&&e.type!=='radio').length""")
    R['PA01_small_targets_login']=small
    R['PA01_lang']=pg.evaluate("document.documentElement.lang")
    R['PA01_viewport_meta']=pg.evaluate("!!document.querySelector('meta[name=viewport]')")
    R['console_errors']=errs
    # PR-01: load with 1 Mbps throttling
    ctx2=b.new_context(viewport={'width':390,'height':844}); pg2=ctx2.new_page()
    cdp=ctx2.new_cdp_session(pg2); cdp.send('Network.enable')
    cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':300,'downloadThroughput':1_000_000/8,'uploadThroughput':500_000/8})
    ts=[]
    for _ in range(3):
        t=time.time(); pg2.goto(URL, wait_until='load'); pg2.wait_for_selector('#lu'); ts.append(round(time.time()-t,2))
    R['PR01_load_1mbps_s']=ts
    b.close()
# contrast
def lum(h):
    h=h.lstrip('#'); r,g,bb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(bb)
def cr(a,b_):
    la,lb=lum(a),lum(b_); 
    if la<lb: la,lb=lb,la
    return round((la+0.05)/(lb+0.05),2)
R['contrast']={'texto/fondo claro':cr('#1b2530','#f4f7fa'),'boton blanco/teal':cr('#ffffff','#0b6e70'),'encabezado blanco/azul':cr('#ffffff','#12355b'),'boton am texto/ambar':cr('#222222','#f2a900'),'tag Recordar':cr('#ffffff','#6b7280'),'tag Evaluar':cr('#ffffff','#c2410c')}
json.dump(R,open('tests/resultados.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(R,ensure_ascii=False,indent=1))
