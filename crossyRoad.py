from cmu_graphics import *
import random

def onAppStart(app):
    # --- High Score Persistence ---
    # We only reset highScore if it doesn't exist yet. 
    # This prevents 'r' from wiping the best score.
    if not hasattr(app, 'highScore'):
        app.highScore = 0
        
    app.gridSize = 40
    app.cols = 11  
    app.width = app.cols * app.gridSize
    app.height = 600
    
    app.playerRow = 3
    app.playerCol = 5.0 
    app.score = 0
    app.gameOver = False
    app.isDrowning = False
    
    app.scrollOffset = 0
    app.rows = []
    
    # Generate initial terrain
    for i in range(-5, 15):
        generateRow(app, i)

def generateRow(app, rowIndex):
    rowType = 'grass'
    if rowIndex > 3:
        rand = random.random()
        if rand < 0.4: rowType = 'road'
        elif rand < 0.7: rowType = 'river'
        elif rand < 0.85: rowType = 'rail'
    
    row = {
        'index': rowIndex,
        'type': rowType,
        'obstacles': [],
        'direction': random.choice([-1, 1]),
        'speed': random.choice([0.05, 0.08, 0.12]), 
        'trainTimer': 0,
        'trainActive': False
    }
    
    if rowType == 'grass' and rowIndex > 3:
        for c in range(app.cols):
            if random.random() < 0.2 and not (rowIndex == 4 and c == 5):
                row['obstacles'].append({'col': c, 'width': 1, 'type': 'tree'})
                
    elif rowType == 'road':
        spawnBlockObstacles(app, row, 'car', 2, 0.3)
        
    elif rowType == 'river':
        if random.random() < 0.2:
            row['speed'] = 0 
            spawnBlockObstacles(app, row, 'lilypad', 1, 0.4) 
        else:
            spawnBlockObstacles(app, row, 'log', 3, 0.4) 
            
    elif rowType == 'rail':
        row['speed'] = 0.8 
        row['trainTimer'] = random.randint(100, 300)

    app.rows.append(row)
    app.rows.sort(key=lambda x: x['index'])

def spawnBlockObstacles(app, row, typeName, widthInBlocks, density):
    c = -2 
    while c < app.cols + 3:
        if random.random() < density:
            obs = {
                'col': c, 
                'width': widthInBlocks,
                'type': typeName
            }
            if typeName == 'car':
                obs['color'] = random.choice(['crimson', 'royalBlue', 'darkOrange', 'purple'])
            row['obstacles'].append(obs)
            c += widthInBlocks + random.randint(2, 4) 
        else:
            c += 1

def onStep(app):
    if app.gameOver: return

    # Manage Rows
    if app.rows[0]['index'] < app.playerRow - 10:
        app.rows.pop(0)
    if app.rows[-1]['index'] < app.playerRow + 15:
        generateRow(app, app.rows[-1]['index'] + 1)

    # Move Obstacles
    currentRow = None
    for row in app.rows:
        if row['index'] == app.playerRow: currentRow = row
        
        if row['type'] in ['road', 'river']:
            for obs in row['obstacles']:
                obs['col'] += row['speed'] * row['direction']
                if row['direction'] == 1 and obs['col'] > app.cols + 2:
                    obs['col'] = -obs['width'] - 2
                elif row['direction'] == -1 and obs['col'] < -obs['width'] - 2:
                    obs['col'] = app.cols + 2

        if row['type'] == 'rail':
            row['trainTimer'] -= 1
            if row['trainTimer'] <= 0 and not row['trainActive']:
                row['trainActive'] = True
                startCol = -20 if row['direction'] == 1 else app.cols + 20
                row['obstacles'] = [{'col': startCol, 'width': 15, 'type': 'train'}]
            
            if row['trainActive'] and row['obstacles']:
                train = row['obstacles'][0]
                train['col'] += row['speed'] * row['direction']
                if (row['direction'] == 1 and train['col'] > app.cols + 20) or \
                   (row['direction'] == -1 and train['col'] < -20):
                    row['obstacles'] = []
                    row['trainActive'] = False
                    row['trainTimer'] = random.randint(200, 400)

    # Collision & Floating
    if not currentRow: return
    
    pLeft = app.playerCol + 0.2
    pRight = app.playerCol + 0.8
    pCenter = app.playerCol + 0.5
    
    if currentRow['type'] in ['road', 'rail']:
        for obs in currentRow['obstacles']:
            oLeft = obs['col']
            oRight = obs['col'] + obs['width']
            if (pLeft < oRight and pRight > oLeft):
                app.gameOver = True

    elif currentRow['type'] == 'river':
        safe = False
        for obs in currentRow['obstacles']:
            oLeft = obs['col']
            oRight = obs['col'] + obs['width']
            if (pCenter > oLeft - 0.1 and pCenter < oRight + 0.1):
                safe = True
                app.playerCol += currentRow['speed'] * currentRow['direction']
                break
        
        if not safe:
            app.gameOver = True
            app.isDrowning = True

    if app.playerCol < -0.5 or app.playerCol > app.cols - 0.5:
        app.gameOver = True

    # Camera
    targetY = (app.playerRow * app.gridSize) - (app.height / 2)
    app.scrollOffset += (targetY - app.scrollOffset) * 0.1

def onKeyPress(app, key):
    if app.gameOver:
        if key == 'r': onAppStart(app)
        return

    targetRow = app.playerRow
    targetCol = app.playerCol
    
    if key == 'left':   targetCol -= 1
    elif key == 'right': targetCol += 1
    elif key == 'up':
        targetRow += 1
        targetCol = int(app.playerCol + 0.5) 
    elif key == 'down':
        targetRow -= 1
        targetCol = int(app.playerCol + 0.5)

    targetRowObj = None
    for r in app.rows:
        if r['index'] == targetRow: targetRowObj = r
            
    if targetRowObj and targetRowObj['type'] == 'grass':
        checkCol = int(targetCol + 0.5)
        for obs in targetRowObj['obstacles']:
            if int(obs['col']) == checkCol:
                return 
                
    app.playerRow = targetRow
    app.playerCol = targetCol 
    
    # Update Score and High Score
    if app.playerRow > app.score: 
        app.score = app.playerRow
        if app.score > app.highScore:
            app.highScore = app.score

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='black')
    
    for row in app.rows:
        screenY = app.height - (row['index'] * app.gridSize) + app.scrollOffset - app.gridSize
        if screenY < -50 or screenY > app.height + 50: continue
        
        if row['type'] == 'grass':
            for c in range(app.cols + 2):
                if (row['index'] + c) % 2 == 0: gColor = 'lightGreen'
                else: gColor = 'paleGreen'
                drawRect(c * app.gridSize, screenY, app.gridSize, app.gridSize, fill=gColor)
                
        elif row['type'] == 'road':
            drawRect(0, screenY, app.width, app.gridSize, fill='dimGray')
            centerY = screenY + app.gridSize / 2
            for i in range(0, int(app.width), 40):
                drawLine(i + 10, centerY, i + 30, centerY, fill='white', lineWidth=3)
                
        elif row['type'] == 'river':
             drawRect(0, screenY, app.width, app.gridSize, fill='deepSkyBlue')
             
        elif row['type'] == 'rail':
             drawRect(0, screenY, app.width, app.gridSize, fill='sandyBrown')
             drawLine(0, screenY+10, app.width, screenY+10, fill='gray', lineWidth=2)
             drawLine(0, screenY+30, app.width, screenY+30, fill='gray', lineWidth=2)
             for i in range(0, app.width, 20):
                 drawLine(i, screenY, i, screenY+app.gridSize, fill='sienna', lineWidth=2)
             lc = 'red' if (row['trainTimer'] < 60 and (row['trainTimer']//5)%2==0) else 'black'
             drawCircle(20, screenY+20, 8, fill=lc, border='white')

        for obs in row['obstacles']:
            screenX = obs['col'] * app.gridSize
            w = obs['width'] * app.gridSize
            
            if obs['type'] == 'tree':
                drawRect(screenX+5, screenY-10, w-10, app.gridSize+10, fill='forestGreen')
                drawRect(screenX+15, screenY+20, 10, 20, fill='sienna')
                
            elif obs['type'] == 'car':
                cColor = obs.get('color', 'blue')
                drawRect(screenX+5, screenY+28, 8, 6, fill='black')
                drawRect(screenX+w-13, screenY+28, 8, 6, fill='black')
                drawRect(screenX, screenY+5, w, 25, fill=cColor)
                drawRect(screenX+5, screenY+8, w-10, 18, fill='lightBlue')
                if row['direction'] == 1:
                    drawRect(screenX+w-2, screenY+7, 2, 5, fill='yellow')
                    drawRect(screenX+w-2, screenY+22, 2, 5, fill='yellow')
                    drawRect(screenX, screenY+7, 2, 5, fill='red')
                    drawRect(screenX, screenY+22, 2, 5, fill='red')
                else:
                    drawRect(screenX, screenY+7, 2, 5, fill='yellow')
                    drawRect(screenX, screenY+22, 2, 5, fill='yellow')
                    drawRect(screenX+w-2, screenY+7, 2, 5, fill='red')
                    drawRect(screenX+w-2, screenY+22, 2, 5, fill='red')

            elif obs['type'] == 'log':
                drawRect(screenX, screenY+5, w, 30, fill='sienna', border='black')
                drawLine(screenX, screenY+15, screenX+w, screenY+15, fill='saddleBrown')
                
            elif obs['type'] == 'lilypad':
                drawCircle(screenX+20, screenY+20, 18, fill='limeGreen')
                drawCircle(screenX+20, screenY+20, 14, fill='lightGreen')
                
            elif obs['type'] == 'train':
                drawRect(screenX, screenY+2, w, 36, fill='crimson', border='white')
                for i in range(0, int(w), 40):
                    drawRect(screenX+i+5, screenY+8, 30, 20, fill='yellow')

    # Player
    pScreenX = app.playerCol * app.gridSize
    pScreenY = app.height - (app.playerRow * app.gridSize) + app.scrollOffset - app.gridSize
    
    if not app.isDrowning:
        drawOval(pScreenX+20, pScreenY+35, 30, 10, fill='black', opacity=30)
        drawRect(pScreenX+5, pScreenY+5, 30, 30, fill='white')
        drawRect(pScreenX+15, pScreenY+2, 10, 5, fill='red')
        drawRect(pScreenX+18, pScreenY+15, 4, 4, fill='black')
        drawPolygon(pScreenX+15, pScreenY+25, pScreenX+25, pScreenY+25, pScreenX+20, pScreenY+32, fill='orange')

    # --- UI UPDATES ---
    
    # 1. In-Game Score (Top Left with Background)
    if not app.gameOver:
        # Semi-transparent background box
        drawRect(10, 10, 140, 40, fill='black', opacity=60, border='white', borderWidth=2)
        drawLabel(f"SCORE: {app.score}", 80, 30, size=24, fill='yellow', bold=True)
    
    # 2. Game Over Screen (Score + High Score)
    else:
        # Box
        boxW, boxH = 300, 160
        drawRect(app.width/2 - boxW/2, app.height/2 - boxH/2, boxW, boxH, fill='white', border='black', borderWidth=3)
        
        # Text
        drawLabel("GAME OVER", app.width/2, app.height/2 - 40, size=35, bold=True, fill='black')
        drawLabel(f"Final Score: {app.score}", app.width/2, app.height/2, size=20, fill='dimGray')
        drawLabel(f"TOP SCORE: {app.highScore}", app.width/2, app.height/2 + 25, size=20, fill='gold', bold=True, border='black', borderWidth=1)
        
        drawLabel("Press 'r' to restart", app.width/2, app.height/2 + 55, size=15, fill='black', italic=True)

runApp(width=440, height=600)