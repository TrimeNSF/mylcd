已完成工能
1、完成英文小字体(5*8)的支持（模式1）
2、完成英文中字体(8*16)的支持（模式2）
3、完成中文字体的支持(16*16)的支持（模式3）
4、完成中文字体的支持or英文中字体的兼容(16*16)的支持（模式3）
5、完成了划线制图（任意起始位置）
6、屏幕显示180转向
7、动态刷新(接收一条刷一次)
8、支持空格,换行（其他的特殊字符暂时不支持）

待完成功能
1、中文字符任意点启始输入
2、变量的封装，buf大小的统一
3、字库的文件查找
4、其他语言的支持
//====================================================================
使用说明:
一、启动服务程序
cd ~/YMX_code/lcd/JLX12864_710_PN/C-006/Service
nohup ./sh.sh > /dev/null&
二、启动客户端传参
cd ~/YMX_code/lcd/JLX12864_710_PN/C-006/Client
./client position_x position_y mode buf_data            // x和y为其实坐标，mode控制方式，buf为传输数据
参数详解：（参数分割符为空格0x20）
position_x:				// 启始位置坐标 x 轴
    在字符串传输为字符串启始位置坐标的 x 轴，取值范围为(64/单位字体x轴的宽度)
    在画图模式为画图启始点的坐标，取值范围为（0~63）
position_y:				// 起始位置坐标 y 轴
    在字符串传输为字符串启始位置坐标的 y 轴，取值范围为(128/单位字体y轴的宽度)
    在画图模式为画图启始点的坐标，取值范围为（0~127）
 mode ：					// 控制方式
    #define LCD_mode_AT                         0       // 指令模式预留（清屏模式已合并到划线模式中）
    #define LCD_mode_table_5x8                  1       // ASCII    5*8
    #define LCD_mode_table_8x16                 2       // ASCII    8*16
    #define LCD_mode_table_16x16                3       // GB3212(16x16) add ASCII(8x16)
    #define LCD_mode_table_image                4       // 画图划线
    #define LCD_mode_table_Make_words           5       // 特殊字符支持(信号)
 buf_data:              // 数据
    LCD_mode_AT：为配置液晶操作（预留）
        0 0 0 0,0   为过滤器的数据头，使用过滤器时，每次界面改变改变(更新或刷新)必须使用调用，否则内存溢出
    LCD_mode_table_5x8：需要显示的缓存数据
    LCD_mode_table_8x16：需要显示的缓存数据
    LCD_mode_table_16x16：需要显示的缓存数据
    LCD_mode_table_image：画图模式，buf有三个数据组成(x_end,y_end,单位颜射：0为暗，1为亮)，分隔符为 ','逗号
        例如：
            清屏：0 0 4 64,128,0
            满屏：0 0 4 64,128,1
    LCD_mode_table_Make_words:特殊符号支持：
        x y mode sub_mode,parameter...
            信号:0 0 5 0,5
            

关于函数传参问题：
    // 执行函数 bug参数
    ./main bug
        bug:没有参数，无log输出
        bug:0,无log输出
        bug:1,log打印输出
      
      
      
1、加快清屏
2、合并头指令
3、log再优化
