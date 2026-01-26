import curses
import random
import time

def main(stdscr):
    # Настройки curses
    curses.curs_set(0)  # Скрыть курсор
    stdscr.nodelay(True)  # Не ждать ввода
    stdscr.timeout(50)  # Задержка обновления
    
    # Инициализация цветов
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)

    sh, sw = stdscr.getmaxyx()
    
    # Состояние колонок: [текущая_строка, скорость, длина_хвоста]
    columns = [[random.randint(-sh, 0), random.randint(1, 2), random.randint(5, sh)] for _ in range(sw)]
    
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$+-*/=%\"'#&_(),.;:?!\\|{}<>[]^~"

    while True:
        stdscr.erase()
        
        for i in range(sw):
            y, speed, length = columns[i]
            
            # Рисуем хвост
            for j in range(length):
                pos_y = y - j
                if 0 <= pos_y < sh:
                    char = random.choice(chars)
                    if j == 0:
                        stdscr.addstr(pos_y, i, char, curses.color_pair(2) | curses.A_BOLD)
                    else:
                        stdscr.addstr(pos_y, i, char, curses.color_pair(1))
            
            # Обновляем позицию
            columns[i][0] += speed
            
            # Если хвост ушел за экран, сбрасываем колонку
            if columns[i][0] - length > sh:
                columns[i] = [0, random.randint(1, 2), random.randint(5, sh)]

        stdscr.refresh()
        
        # Выход по нажатию 'q'
        key = stdscr.getch()
        if key == ord('q'):
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
