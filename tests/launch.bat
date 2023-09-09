chcp 65001

:loop
    python ../src/main.py calc.ods sh1 -t data_calc_raw.tex
    pause
    goto loop

