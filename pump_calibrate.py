from tkinter import *
from threading import Timer
from math import fmod
from matplotlib.pyplot import figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import time
import serial as sr   # 需要安装这个模块，pip3 install pyserial
import matplotlib.pyplot as plt
import tkinter.messagebox as mb

# 初始化变量
cycle = 0
point = 0             # 控制开关，默认为0，手动控制为1，PID控制为2
time_list = []
SYB_list = []
online_NB = [0]
online_MA = [0]
online_SYB_list = []
delta_t = 30000    # 标泵间隔
# PID控制变量
curValueList = []   # 被控对象输出
timeList = []
setValueList = []
PIDoutList = []     # PID输出
curValueList.append(0) # 先加入一个0打底
timeList.append(0)     # 先加入一个0打底
PIDoutList.append(0)               # 先加入一个0打底
setValueList.append(1.2)
curValue = 0        # 目标的当前值，也就是当前酸油比
NB1,MA1 = 0,0
# 打开交互作图模式
plt.close()    #   clf() # 清图  cla() # 清坐标轴 close() # 关窗口
plt.ion()      #   interactive mode on

# 自定义一个frame类
class PC(Frame):
    def __init__(self, name):
        self.name = name
        Frame.__init__(self)
        self._start = 0.0              # 私有 开始时间设为 0
        self._passtime = 0.0           # 已经过去了的时间设为 0
        self._isRunning = False        # 秒表是否在运行 默认为否
        self.timestr = StringVar()     # 时间字符串
    # 设置窗口    
    def setwindow(self):
        # 声明以下全局变量
        global v1,v2,v3,v4,a,b,c,d,e,f,g,h,onlinev1,onlinev2,Q_display,Q_set,point
        # 设置窗口信息
        self.name.title("标泵小程序_Zwy&Meng")
        self.name.geometry('1200x500')
        # 变量
        v1 = StringVar()
        v2 = StringVar()
        v3 = StringVar()
        v4 = StringVar()
        onlinev1 = StringVar()
        onlinev2 = StringVar()
        Q_display = StringVar() # 显示流量
        Q_set = DoubleVar()     # 设置流量
        point = IntVar()     # 设置判断值
        e  = DoubleVar()
        g  = DoubleVar()   # SYB设定值
        h  = DoubleVar()
        f  = '1B70'
        v1.set('0g')
        v2.set('0g')
        v3.set('1g')
        v4.set('1g')
        onlinev1.set('0g')
        onlinev2.set('0g')
        e .set('0.0')
        g .set('0.0')   # 设定酸油比
        # 标签
        self.csz = Label(self.name, text='初始值', fg='black',font=('微软雅黑',20))
        self.csz.place(x = 100,y = 30,width = 80, height = 60)
        self.zlz = Label(self.name, text='终了值', fg='black',font=('微软雅黑',20))
        self.zlz.place(x = 300,y = 30,width = 80, height = 60)
        self.jsq = Label(self.name, textvariable=self.timestr, width = 15)
        self._setTime(self._passtime)
        self.jsq.place(x = 300,y = 300,width = 80, height = 30)
        self.SYB = Label(self.name, text='请输入酸油比：', fg='black',font=('微软雅黑',12))
        self.SYB.place(x = 1050,y = 10,width = 150, height = 30)
        self.setPump = Label(self.name, text='设置泵流量：', fg='black',font=('微软雅黑',12))
        self.setPump.place(x = 1050,y = 150,width = 150, height = 30)
        self.onlinePump = Label(self.name, text='实时泵流量：', fg='black',font=('微软雅黑',12))
        self.onlinePump.place(x = 1050,y = 300,width = 150, height = 30)
        # 按钮
        self.sj1 = Button(self.name, text='获取数据', fg = 'red', command=self.serial1)
        self.sj1.place(x = 100,y = 200,width = 80, height = 30)
        self.sj2 = Button(self.name, text='获取数据', fg = 'red', command=self.serial2)
        self.sj2.place(x = 300,y = 200,width = 80, height = 30)
        self.bb = Button(self.name, text='标泵', fg = 'red', command=self.calculate)
        self.bb.place(x = 100,y = 250,width = 80, height = 30)
        self.js = Button(self.name, text='计时', fg = 'red', command=self.begin)
        self.js.place(x = 100,y = 300,width = 80, height = 30)
        self.zt = Button(self.name, text='暂停', fg = 'red', command=self.stop)
        self.zt.place(x = 300,y = 350,width = 80, height = 30)
        self.cxjs = Button(self.name, text='重新计时', fg = 'red', command=self.reset)
        self.cxjs.place(x = 100,y = 350,width = 80, height = 30)
        self.gy = Button(self.name, text='关于', fg = 'red', command=self.show_msg)  # 万万注意 必须是self.函数名 ，只有函数名是没有定义的
        self.gy.place(x = 100,y = 400,width = 80, height = 30)
        self.tc = Button(self.name, text='退出', fg = 'red', command=self.name.quit)
        self.tc.place(x = 300,y = 400,width = 80, height = 30)  #, command=self.quit
        self.manual_Control = Button(self.name, text='手动控制(默认)', fg = 'red', command=self.manualControl)
        self.manual_Control.place(x = 1075,y = 100,width = 100, height = 30)
        self.begin_PID = Button(self.name, text='PID控制', fg = 'green', command=self.beginPID)
        self.begin_PID.place(x = 1075,y = 250,width = 100, height = 30)
        self.stop_PID = Button(self.name, text='导出进料比', fg = 'black', command=self.stopPID)
        self.stop_PID.place(x = 1075,y = 400,width = 100, height = 30)
        # Entry
        self.hs1 = Entry(self.name, width = 10, textvariable = v1, justify='center')
        self.hs1.place(x = 100,y = 150,width = 80, height = 30)
        self.nb1 = Entry(self.name, width = 10, textvariable = v2, justify='center')
        self.nb1.place(x = 100,y = 100,width = 80, height = 30)
        self.hs2 = Entry(self.name, width = 10, textvariable = v3, justify='center')
        self.hs2.place(x = 300,y = 150,width = 80, height = 30)
        self.nb2 = Entry(self.name, width = 10, textvariable = v4, justify='center')
        self.nb2.place(x = 300,y = 100,width = 80, height = 30)        
        self.bbz = Entry(self.name, width = 10, textvariable = e, justify='center')    # 标泵计算值
        self.bbz.place(x = 300,y = 250,width = 80, height = 30)
        self.syb = Entry(self.name, width = 10, validate='key',textvariable = g, justify='center')  # 酸油比设定值
#         self.syb.bind('<Enter>', self.rtnkey())
        self.syb.place(x = 1075,y = 50,width = 100, height = 30)
        # 手动设定泵流量
        self.setQ = Entry(self.name, width = 10, textvariable = Q_set, justify='center')
        self.setQ.place(x = 1075,y = 200,width = 100, height = 30)
        # 实时显示泵流量
        self.displayQ = Entry(self.name, width = 10, textvariable = Q_display, justify='center')
        self.displayQ.place(x = 1075,y = 350,width = 100, height = 30)

    # 关于函数
    def show_msg(self):
        mb.showinfo('关于','这是由赵文远制作的小程序 3.0')
        
    # hex编码函数
    def hexsend(self):
        hex_data = bytes.fromhex(f)    # f=1B70 在这里转化为16进制hex码
        return hex_data
    
    # 串口通信函数
    def serial1(self):
        # 删除数据1函数
        self.hs1.delete(0,END)
        self.nb1.delete(0,END)
        ser1 = sr.Serial("COM3",600,timeout=0.5)
        ser2 = sr.Serial("COM4",600,timeout=0.5)
#         ser1.write(self.hexsend('1B70'))  # 这里有引号吗？
#         ser2.write(self.hexsend('1B70'))
        ser1.write(self.hexsend())  
        ser2.write(self.hexsend())
        v1.set(ser1.readline())
        v2.set(ser2.readline())
        ser1.close()
        ser2.close()
    
    # 串口通信函数
    def serial2(self):
        # 删除数据2函数
        self.hs2.delete(0,END)
        self.nb2.delete(0,END)
        ser3 = sr.Serial("COM3",600,timeout=0.5)
        ser4 = sr.Serial("COM4",600,timeout=0.5)
        ser3.write(self.hexsend())  
        ser4.write(self.hexsend())
        v3.set(ser3.readline())
        v4.set(ser4.readline())
        ser3.close()
        ser4.close()

    # 计算函数  
    def calculate(self):
        self.bbz.delete(0,END)
        # strip 删除字符串头尾指定的字符,但是注意这里必须先删除\n,\r再才能再删除g，不然一下子删不掉g，因为strip只能删除末尾的，不可以删除中间的g，因为末尾是\r \n
        a = float(self.hs1.get().strip().strip('g').strip('-'))  
        b = float(self.nb1.get().strip().strip('g').strip('-'))
        c = float(self.hs2.get().strip().strip('g').strip('-'))
        d = float(self.nb2.get().strip().strip('g').strip('-'))
        e = round((c-a)/(d-b),3)              # 设置小数点后三位
        self.bbz.insert(0, e)

    # 设定时间
    def _setTime(self, passTime):
        minutes = int(passTime/60)
        seconds = int(passTime - minutes * 60.0)
        mseconds = int((passTime - minutes * 60.0 - seconds) * 10)
        self.timestr.set('%02d:%02d.%01d' % (minutes, seconds, mseconds))

    # 更新时间
    def _update(self):
        self._passtime = time.time() - self._start
        self._setTime(self._passtime)
        self.timer = self.after(100, self._update)     # 每 100ms 更新一次

    # 开始
    def begin(self):
        if not self._isRunning:
            self._start = time.time() - self._passtime
            self._update()
            self._isRunning = True

    # 停止
    def stop(self):
        if self._isRunning:
            self.after_cancel(self.timer)
            self._passtime = time.time() - self._start
            self._setTime(self._passtime)
            self._isRunning = False

    # 重设
    def reset(self):
        if not self._isRunning:           # 设置只有在秒表停止后 reset 才起作用
            self._start = time.time()
            self._passtime = 0.0
            self._setTime(self._passtime)
            
    # 开始采用PID调节      
    def beginPID(self):
        global point
        point.set('2')         # 这里设定的point只要大于1即可
        
    def stopPID(self):
        pass
    
    # 停止PID调节，采用手动，并获取当前流量
    def manualControl(self):
        global point
        point.set('1')        # 这里设定的point只要不大于1即可
        Q_display.set(flux_get())
        
    # syb.Entry 绑定快捷键
    def rtnkey(event=None):
        global h               # h必须在这里声明，而不是前边
        h.set(g.get()) 

# 获取泵当前流量的函数
def flux_get():
    global flux
    # 固定读取泵命令：2132303030342020202020203231350A  # 实际上就是中间value“保留”即可，我弄的是 “SP SP SP SP SP SP”
    read_flux = '2132303030342020202020203231350A'
    ser0 = sr.Serial('COM3',9600,timeout=1)
    ser0.write(bytes.fromhex(read_flux))
    flux_get = ser0.readline()
#     print(flux_get,type(flux_get))
    ser0.close()
    if flux_get == '$':
        mb.showerror('操作提示','流量读取失败！')
    elif flux_get  == ' ':
        mb.showwarning('操作提示','串口读取通讯失败~')
    str_flux = str(flux_get).strip('b').strip("'").strip('!').strip()  # 这里的！要加上双引号
    flux = str_flux[7:11]
    flux_list = list(flux)
    flux_list.insert(2 , '.')
    flux = "".join(flux_list)
#     print(type(flux))
    return flux

# 调整泵流量为PIDout
def flux_set(PIDout):
    # 从DoubleString到16位命令
#     flow_set.set(PIDout)
    PIDout = '%.2f' % PIDout        # 保证一定有两位小数
    flux_str = str(PIDout)
    Q_display.set(flux_str)         # 显示实时流量
    print('流量设置为：',flux_str)
    flux_list = list(flux_str)
    flux_list.remove('.')
#     print(flux_list)
    if len(flux_list) < 4:         # 保证如果流量小于十位数，前边会自动补一个0
        flux_list.insert(0,'0')
    flux_str = "".join(flux_list)
#     print(type(flux_str),flux_str,'\n',flux_list)
    # 随动计算CRC，生成实时修改泵流量命令
    # 随动设定泵命令：2132303031302020XXXXcrc0A 
    # flux_str 转化为value命令
    flux_list_hex = [str(int(x)+30) for x in flux_list]
    flux_str_hex = "".join(flux_list_hex)
#     print(flux_list_hex,'\n',flux_str_hex)
    # CRC计算
    flux_list_crc = [int(x)+48 for x in flux_list]
#     print(flux_list_crc)
    # 对于纯数字采用格式化的方法来补0到三位数
    crc_str = "%03d" % int(fmod(33+50+48+48+49+48+32+32+sum(flux_list_crc),256)) 
    crc_list = list(crc_str)
    crc_list_hex = [str(int(x)+30) for x in crc_list]
#     print(crc_list,crc_str,crc_list_hex)
    request = "".join(['2132303031302020'] + flux_list_hex + crc_list_hex + ['0A']) # 要输入的命令
#     print(request)
    ser = sr.Serial('COM3',9600,timeout=1)
    ser.write(bytes.fromhex(request))
    set_back = ser.readline()
#     print(set_back,type(set_back))
    ser.close()
    if set_back == '$':
        mb.showerror('操作提示','流量读取失败！')
    elif set_back  == ' ':
        mb.showwarning('操作提示','串口读取通讯失败~')

# 读取称值
def scale_display():    
    seronline1 = sr.Serial("COM4",600,timeout=0.5)
    seronline2 = sr.Serial("COM5",600,timeout=0.5)
    seronline1.write(bytes.fromhex('1B70'))  
    seronline2.write(bytes.fromhex('1B70'))
    NB = seronline1.readline()
    MA = seronline2.readline() 
    seronline1.close()
    seronline2.close()
    print(str(NB))
    a = float(str(NB).strip('b').strip("''").strip().strip('\\n').strip('\\r').strip().strip('g'))
    b = float(str(MA).strip('b').strip("''").strip().strip('\\n').strip('\\r').strip().strip('g'))
    return a,b

class PID:
    def __init__(self, P=0.2, I=0.0, D=0.0):
#         global sleep_t
        self.kp = P
        self.ki = I
        self.kd = D
        self.uPrevious = 0
        self.uCurent = 0
        self.setValue = 0
        self.lastErr = 0
        self.preLastErr = 0
        self.errSum = 0
        self.errSumLimit = 10
        
# 位置式PID
    def pidPosition(self, curValue):
        err = self.setValue - curValue
        dErr = err - self.lastErr
        self.preLastErr = self.lastErr
        self.lastErr = err
        self.errSum += err
        outPID = self.kp * err + (self.ki * self.errSum) + (self.kd * dErr)
        return outPID
    
# 增量式PID
    def pidIncrease(self, curValue):
        self.uCurent = self.pidPosition(curValue)
        outPID = self.uCurent - self.uPrevious
        self.uPrevious = self.uCurent
        return outPID             # 这里返回的我猜是要设定流量的值，而非要增加或者减少的流量

# 实现PID控制
def testPid(P=1, I=0.1, D=0.1):
    global curValue,curValueList,timeList,PIDoutList,setValueList,NB1,MA1,afterHandler,cycle,point
    pid = PID(P, I, D)
#     pid.setValue = 1.2    # 目标设定被控要达到的值，也就是设定酸油比
    try:
        pid.setValue = float(pump_calibrate.syb.get())    # 目标设定被控要达到的值，也就是设定酸油比
        print("已取得输入:",pid.setValue)
    except (ValueError):
        pid.setValue = 1.2    # 目标设定被控要达到的值，也就是设定酸油比
        print("程序发生了数字格式异常，自动设置酸油比为1.2")
    except :
        print("未知异常")
    cycle += 1
    #采用位置式PID去掉注释即可
    # outPID = pid.pidPosition(curValue)
    NB2,MA2 = scale_display()
    if abs((MA1-MA2)) <= 1 or abs(NB1-NB2) <= 1:
        mb.showwarning('操作提示','Scale数值无变化')
    else:
        curValue = (MA1-MA2)/(NB1-NB2)
        if point.get() > 1:   # point这个值是为了设定PID控制的开关
            print('已开始PID控制',point.get() )
            outPID = pid.pidIncrease(curValue)   # 增量式PID，接收当前值(也就是标泵值)，输出一个差值
            PIDoutList.append(outPID)            # 接收差值，增量控制后输出
    #         flux_set(PIDout)                                   # 这里的PIDout式直接set还是再加上基础值？
#             print(flux_get(),type(flux_get()))
            flux = float(flux_get())
            flux_set(outPID+flux)                                   # 这里的PIDout式直接set还是再加上基础值？
        else:
            print('当前为手动控制',point.get())
            PIDoutList.append('None')
        NB1,MA1 = scale_display()
        curValueList.append(curValue)
        setValueList.append(pid.setValue)
        timeList.append(cycle*(delta_t/60000)) # 这里的单位是分钟
    # 尝试绘图
    plt.cla()          # 清除之前的plt.text，保持只有最后一个点plot
    plt.xlabel('time (min)')
    plt.ylabel('set value')
    plt.title('PID')
    plt.scatter(timeList,curValueList,c='b',marker='.')  # 散点图
    plt.plot(timeList,curValueList,c='r')                # 连线图
    plt.plot(timeList,setValueList,c='b')                # 设定值图直线
    plt.xlim((0, max(timeList)*1.2))                 # 这里的1.2指的是右边多0.2最大值的比例
    plt.ylim((min(curValueList)-5, max(curValueList)+6))
    plt.text(timeList[-1],curValueList[-1],"%.2f" % curValueList[-1],family='Consolas',fontsize=14,color='r')
    plt.grid(True) #添加网格
    canvas.draw()
    afterHandler = root.after(delta_t, testPid)

# 关闭窗口
def on_closing():
    root.after_cancel(afterHandler)
    answer = mb.askokcancel("退出", "确定退出吗?")
    if answer:
        plt.close('all')
        root.destroy()
    else:
        root.after(100000000, testPid())

# 创建主窗口
root = Tk()
pump_calibrate = PC(root)
pump_calibrate.pack(side=LEFT, padx=5, pady=5)
pump_calibrate.setwindow()

pump_pid = Frame(root,width=600, height=500, relief=GROOVE, borderwidth=5)
pump_pid.place(x=450,y=0)

fig = plt.figure(figsize=(4,3.25),dpi=150)
canvas = FigureCanvasTkAgg(fig,master = pump_pid)
# onlineCalibrate()
# testPid(1, 0.1, 0.1)
canvas.get_tk_widget().place(x=0, y=0)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()