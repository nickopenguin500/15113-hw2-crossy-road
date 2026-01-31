from cmu_graphics import *
import random

def onAppStart(app):
    # --- Game Constants ---
    app.gridSize = 40
    app.rows = [] # Stores the terrain strips
    app.width = 400
    app.height = 600
    app.scrollOffset = 0
    app.score = 0
    app.gameOver = False
    
    # --- Player Properties ---
    app.playerRow = 3 # Start slightly up
    app.playerCol = 5 # Center (assuming 10 cols)
    app.playerX = app.playerCol * app.gridSize
    app.playerY = app.height - (app.playerRow * app.gridSize)
    app.isDrowning = False
    
    # --- Visuals ---
    app.chickenColor = 'white'
    app.stepsTaken = 0 # To track unique forward progress
    
    # Generate initial buffer of terrain
    # We generate "negative" rows (upwards) and positive rows (behind)
    for i in range(-5, 15): 
        generateRow(app, i)

def generateRow(app, rowIndex):
    # rowIndex 0 is the start line. Positive goes UP the screen (forward).
    # We map rowIndex to a y-coordinate relative to the world.
    
    rowType = 'grass'
    
    # Logic to randomize terrain, keeping start area safe
    if rowIndex > 3:
        rand = random.random()
        if rand < 0.4: rowType = 'road'
        elif rand < 0.7: rowType = 'river'
        elif rand < 0.85: rowType = 'rail'
        else: rowType = 'grass'
    
    # Create the row dictionary
    row = {
        'index': rowIndex,
        'type': rowType,
        'obstacles': [], # Cars, logs, trains
        'direction': random.choice([-1, 1]), # 1 = Right, -1 = Left
        'speed': random.randint(2, 6),
        'timer': 0, # Used for train lights
        'trainActive': False
    }
    
    # Populate obstacles based on type
    if rowType == 'road':
        populateRoad(app, row)
    elif rowType == 'river':
        row['speed'] = random.randint(2, 4) # Logs move slower usually
        populateRiver(app, row)
    elif rowType == 'rail':
        row['speed'] = 25 # Super fast
        row['trainTimer'] = random.randint(100, 300) # Random time until train
        
    # Add trees/rocks to grass
    if rowType == 'grass' and rowIndex > 3:
        populateGrass(app, row)
        
    app.rows.append(row)
    # Keep rows sorted by index so drawing order is correct
    app.rows.sort(key=lambda x: x['index'])

def populateRoad(app, row):
    # Add 1-3 cars
    count = random.randint(1, 3)
    minDist = 3 * app.gridSize
    for _ in range(count):
        # Find a spot not overlapping too much
        x = random.randint(-app.width, app.width*2)
        # Simple overlap check could go here, but random scattering usually works for simple clones
        width = random.choice([app.gridSize, app.gridSize*1.5]) # Car vs Truck
        color = random.choice(['red', 'blue', 'orange', 'purple'])
        row['obstacles'].append({
            'x': x, 'width': width, 'color': color, 'type': 'car'
        })

def populateRiver(app, row):
    # Decide: Is this an active river (logs) or a calm patch (lilypads)?
    # 80% chance of Logs (Moving), 20% chance of Lilypads (Static)
    isLogLane = random.random() < 0.8
    
    # Define generation boundaries (extra wide to handle scrolling)
    currentX = -200 
    endX = app.width + 400
    
    row['obstacles'] = []
    
    while currentX < endX:
        if isLogLane:
            oType = 'log'
            color = 'sienna'
            width = random.choice([app.gridSize*2, app.gridSize*3, app.gridSize*4])
            speed = row['speed'] # Logs move
            gap = random.randint(60, 150) # Space between logs to jump
        else:
            oType = 'lilypad'
            color = 'lightGreen'
            width = app.gridSize * 0.8
            speed = 0 # Lilypads are static
            gap = random.randint(40, 60) # Tighter spacing for lilypads
            
        # Add the obstacle
        row['obstacles'].append({
            'x': currentX,
            'width': width,
            'color': color,
            'type': oType,
            'speed': speed
        })
        
        # Advance the cursor so the next item spawns AFTER this one
        currentX += width + gap

def populateGrass(app, row):
    # Add static trees
    count = random.randint(0, 3)
    for _ in range(count):
        col = random.randint(0, 9)
        # Don't block the very first move or create impossible walls ideally
        row['obstacles'].append({
            'col': col, 'type': 'tree'
        })

def onStep(app):
    if app.gameOver: return

    # --- 1. Manage Rows & Generation ---
    # Remove rows that are too far behind (Changed to 20 to fix black bar)
    if len(app.rows) > 0:
        lowestIndex = app.rows[0]['index']
        if lowestIndex < app.playerRow - 20:
            app.rows.pop(0)
    
    # Add rows ahead
    highestIndex = app.rows[-1]['index']
    if highestIndex < app.playerRow + 15:
        generateRow(app, highestIndex + 1)

    # --- 2. Update Obstacles ---
    currentRow = getRowByIndex(app, app.playerRow)

    for row in app.rows:
        # Move Cars and Logs
        if row['type'] in ['road', 'river']:
            for obs in row['obstacles']:
                
                # Get speed (Logs move, Lilypads are 0)
                speed = obs.get('speed', row['speed'])
                obs['x'] += speed * row['direction']
                
                # Wrap around logic (Only for moving items)
                if speed > 0:
                    if row['direction'] == 1 and obs['x'] > app.width + 100:
                        obs['x'] = -200 - obs['width']
                    elif row['direction'] == -1 and obs['x'] < -100 - obs['width']:
                        obs['x'] = app.width + 200

        # Train Logic
        if row['type'] == 'rail':
            row['trainTimer'] -= 1
            if row['trainTimer'] <= 60 and row['trainTimer'] > 0:
                row['trainActive'] = False # Warning phase
            elif row['trainTimer'] <= 0:
                row['trainActive'] = True
                if len(row['obstacles']) == 0:
                    # Spawn train
                    row['obstacles'].append({
                        'x': -1000 if row['direction'] == 1 else app.width + 1000, 
                        'width': app.gridSize * 15, 
                        'type': 'train'
                    })
                
                # Move train
                train = row['obstacles'][0]
                train['x'] += row['speed'] * row['direction']
                
                # Reset if train leaves screen
                if (row['direction'] == 1 and train['x'] > app.width + 1000) or \
                   (row['direction'] == -1 and train['x'] < -1000):
                    row['obstacles'] = []
                    row['trainTimer'] = random.randint(200, 400)
                    row['trainActive'] = False

    # --- 3. Collision Logic ---
    
    # Check bounds (Left/Right side of screen)
    if app.playerCol < 0 or app.playerCol > 9:
        app.gameOver = True 

    if currentRow:
        # ROAD COLLISION
        if currentRow['type'] == 'road':
            for car in currentRow['obstacles']:
                # Simple X-axis overlap check
                if (app.playerX + 5 < car['x'] + car['width'] and 
                    app.playerX + 35 > car['x']):
                    app.gameOver = True
        
        # RAIL COLLISION
        elif currentRow['type'] == 'rail' and len(currentRow['obstacles']) > 0:
            train = currentRow['obstacles'][0]
            if (app.playerX + 5 < train['x'] + train['width'] and 
                app.playerX + 35 > train['x']):
                app.gameOver = True

        # RIVER COLLISION (Fixed for CMU Graphics)
        elif currentRow['type'] == 'river':
            onLog = False
            
            for obs in currentRow['obstacles']:
                # Check bounds
                if (app.playerX + 10 < obs['x'] + obs['width'] and 
                    app.playerX + 30 > obs['x']):
                    onLog = True
                    
                    # Move player visually
                    obsSpeed = obs.get('speed', currentRow['speed'])
                    app.playerX += obsSpeed * currentRow['direction']
                    
                    # FIX: Use 'rounded' instead of 'round'
                    app.playerCol = rounded(app.playerX / app.gridSize)
                    
                    break
            
            if not onLog:
                app.gameOver = True
                app.isDrowning = True
            
            # Die if log carries you off screen
            if app.playerX < -app.gridSize or app.playerX > app.width:
                app.gameOver = True

    # Camera scroll smoothing
    targetScroll = (app.playerRow * app.gridSize) - (app.height / 2)
    app.scrollOffset += (targetScroll - app.scrollOffset) * 0.1

def onKeyPress(app, key):
    if app.gameOver:
        if key == 'r': onAppStart(app)
        return

    dRow, dCol = 0, 0
    if key == 'up':    dRow = 1
    elif key == 'down':  dRow = -1
    elif key == 'left':  dCol = -1
    elif key == 'right': dCol = 1
    
    targetRow = app.playerRow + dRow
    targetCol = app.playerCol + dCol
    
    # Validate Move (Check for trees)
    rowObj = getRowByIndex(app, targetRow)
    if rowObj and rowObj['type'] == 'grass':
        for obs in rowObj['obstacles']:
            if obs['col'] == targetCol:
                return # Blocked by tree
    
    # Commit Move
    app.playerRow = targetRow
    app.playerCol = targetCol
    
    # Snap X position to grid when hopping (removes log drift drift)
    app.playerX = app.playerCol * app.gridSize
    
    # Update score
    if app.playerRow > app.score:
        app.score = app.playerRow

def getRowByIndex(app, index):
    for row in app.rows:
        if row['index'] == index: return row
    return None

def getScreenY(app, rowIndex):
    # Convert logical row index to screen Y coordinate
    # World Y increases as we go UP. Screen Y increases as we go DOWN.
    # Base: app.height. Subtract row*size. Add scroll.
    worldY = rowIndex * app.gridSize
    screenY = app.height - worldY + app.scrollOffset - app.gridSize
    return screenY

def rectanglesOverlap(r1, r2):
    # r1, r2 = (x, y, w, h)
    return (r1[0] < r2[0] + r2[2] and
            r1[0] + r1[2] > r2[0] and
            r1[1] < r2[1] + r2[3] and
            r1[1] + r1[3] > r2[1])

def redrawAll(app):
    drawRect(0, 0, app.width, app.height, fill='black') # Fallback background
    
    # --- Draw Terrain & Obstacles ---
    for row in app.rows:
        screenY = getScreenY(app, row['index'])
        
        # Don't draw if off screen
        if screenY < -50 or screenY > app.height + 50: continue
        
        # 1. Draw Base Terrain
        color = 'lightGreen'
        if row['type'] == 'road': color = 'dimGray'
        elif row['type'] == 'river': color = 'deepSkyBlue'
        elif row['type'] == 'rail': color = 'sandyBrown'
        
        drawRect(0, screenY, app.width, app.gridSize, fill=color)
        
        # Draw Rail Tracks Details
        if row['type'] == 'rail':
            drawLine(0, screenY+10, app.width, screenY+10, fill='gray', lineWidth=2)
            drawLine(0, screenY+30, app.width, screenY+30, fill='gray', lineWidth=2)
            for i in range(0, app.width, 20):
                drawLine(i, screenY, i, screenY+app.gridSize, fill='sienna', lineWidth=2)
                
            # Traffic Light
            lightColor = 'black'
            if row['trainTimer'] < 60 and (row['trainTimer'] // 5) % 2 == 0:
                lightColor = 'red' # Flash red
            drawCircle(20, screenY + 20, 8, fill=lightColor, border='white')

        # 2. Draw Obstacles (Cars, Logs, Trees)
        for obs in row['obstacles']:
            if row['type'] == 'grass' and obs['type'] == 'tree':
                # Draw Tree
                tx = obs['col'] * app.gridSize
                drawRect(tx + 10, screenY + 15, 20, 25, fill='sienna') # Trunk
                drawCircle(tx + 20, screenY + 10, 15, fill='forestGreen') # Leaves
            
            elif obs['type'] == 'car':
                # Draw Car (Simple Box with windows)
                drawRect(obs['x'], screenY + 5, obs['width'], app.gridSize - 10, fill=obs['color'], border='black')
                drawRect(obs['x'] + 5, screenY + 10, obs['width'] - 10, app.gridSize - 20, fill='skyBlue')

            elif obs['type'] == 'log':
                drawRect(obs['x'], screenY + 5, obs['width'], app.gridSize - 10, fill='sienna', border='black')
                
            elif obs['type'] == 'lilypad':
                drawCircle(obs['x'] + obs['width']/2, screenY + app.gridSize/2, obs['width']/2, fill='limeGreen')

            elif obs['type'] == 'train':
                drawRect(obs['x'], screenY + 2, obs['width'], app.gridSize - 4, fill='red', border='white')
                # Windows
                for i in range(0, int(obs['width']), 40):
                    drawRect(obs['x'] + i + 10, screenY + 10, 20, 20, fill='yellow')

    # --- Draw Player ---
    # Player Y is calculated based on row index to keep it synced with scrolling
    # But we use app.playerX which handles the log floating logic
    
    pScreenY = getScreenY(app, app.playerRow)
    
    if not app.isDrowning:
        # Chicken Body
        drawRect(app.playerX + 5, pScreenY + 5, 30, 30, fill='white')
        # Beak
        if app.playerCol < 9: # simplistic direction check or just face forward
            drawRect(app.playerX + 15, pScreenY + 20, 10, 5, fill='orange')
        # Comb
        drawRect(app.playerX + 15, pScreenY + 2, 10, 5, fill='red')
        
    # --- UI ---
    drawLabel(f"Score: {app.score}", 30, 30, size=20, align='left', bold=True, fill='white', border='black')
    
    if app.gameOver:
        drawRect(50, app.height/2 - 50, app.width-100, 100, fill='white', border='black')
        drawLabel("GAME OVER", app.width/2, app.height/2 - 15, size=30, bold=True)
        drawLabel(f"Final Score: {app.score}", app.width/2, app.height/2 + 10, size=20)
        drawLabel("Press 'r' to restart", app.width/2, app.height/2 + 35, size=15)

runApp(width=400, height=600)