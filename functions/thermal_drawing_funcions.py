import matplotlib.pyplot as plt
import matplotlib.colors as mc
from numpy import linspace, array, asarray, concatenate, sqrt, array_equal, append, max, min, argmax, argmin, around, zeros
from pandas import read_csv, DataFrame, Series
from structural_drawing_funcions import coloured_line, check_repeated_lines
import streamlit as st

def thermal_problems(filename, graph, scale, fig, ax, canvas, nodes_check, check_adjust, parallel_adjust, print_test):
    # 'canvas' se mantiene por compatibilidad, pero no se usa .draw()
    file = read_csv(filename, sep = '\t', index_col=False)

    if file['Problema'][0] != 1:
        st.error("Error: El archivo de entrada no pertenece a un problema térmico")
        return

    nel = file['Formulacion'].size
    if parallel_adjust.get() == 1:
        file, elem_list = get_parallel_elements(file)

    # Cálculo de límites del área de dibujo
    xmin = min([file['Xi'].min(), file['Xj'].min()])
    xmax = max([file['Xi'].max(), file['Xj'].max()])
    ymin = min([file['Yi'].min(), file['Yj'].min()])
    ymax = max([file['Yi'].max(), file['Yj'].max()])

    dx = abs(xmax - xmin)
    dy = abs(ymax - ymin)
    if dx == 0: dx = dy
    if dy == 0: dy = dx

    if graph == "Distribucion de Temperatura":
        Smax = max([file['Ti'].max(), file['Tj'].max()])
        Smin = min([file['Ti'].min(), file['Tj'].min()])
        norm = plt.Normalize(Smin, Smax)

        for i in range(nel):
            x = linspace(file['Xi'][i], file['Xj'][i], 10)
            y = linspace(file['Yi'][i], file['Yj'][i], 10)
            S = linspace(file['Ti'][i], file['Tj'][i], 9)
            lc = coloured_line(x, y, S, fig, ax, norm, 'jet')
            line = ax.add_collection(lc)

        if nodes_check.get() == 1:
            # Optimización: Dibujar todos los nodos en una sola llamada
            ax.scatter(append(file['Xi'], file['Xj']), append(file['Yi'], file['Yj']), 
                       color='black', s=1.5, zorder=2)
        
        cbar = plt.colorbar(line, ax=ax, shrink=0.8)
        cbar.set_ticks(linspace(Smin, Smax, 8))
        plt.title(f"File: {filename.split('/')[-1]}\nDistribución de temperatura", fontsize=7.5)
        plt.xlabel('X')
        plt.ylabel('Y')
        ax.set_xlim(xmin-dx/nel, xmax+dx/nel)
        ax.set_ylim(ymin-dy/nel, ymax+dy/nel)

    elif graph == "Malla de Elementos Finitos":
        draw_mesh(nel, file, filename, "\nMalla de Elementos Finitos", ax, xmax, xmin, ymax, ymin, dx, dy)

    elif graph == "Distribucion de Calor por Conduccion":
        save_heat_plot(fig, ax, file, filename, nel, xmax, xmin, ymax, ymin, dx, dy, "\nDistribución de calor por conducción", 'Qcond', nodes_check)
    
    elif graph == "Distribucion de Calor por Conveccion":
        save_heat_plot(fig, ax, file, filename, nel, xmax, xmin, ymax, ymin, dx, dy, "\nDistribución de calor por convección", 'Qconv', nodes_check)

    elif "Diagrama" in graph:
        map_vars = {
            "Diagrama de Temperatura": ("Temp", "_diag_temp", "Red"),
            "Diagrama de Calor por Conduccion": ("Qcond", "_diag_qcond", "Blue"),
            "Diagrama de Calor por Conveccion": ("Qconv", "_diag_qconv", "Green")
        }
        var_type, f_name, color_diag = map_vars[graph]
        HT_diagrams(fig, ax, file, filename, f_name, f"\n{graph}", canvas, color_diag, xmax, xmin, dx, nel, var_type, nodes_check, scale, check_adjust, parallel_adjust, print_test)

    # --- RENDERIZADO FINAL EN STREAMLIT ---
    st.pyplot(fig)
    
    if print_test.get() == 1:
        img_name = filename.split('.eplot')[0] + "_output.png"
        plt.savefig(img_name, dpi=720)
        st.success(f"Imagen generada con éxito")

def draw_mesh(nel, file, filename, fig_title, ax, xmax, xmin, ymax, ymin, dx, dy):
    for i in range(nel):
        x_elem = array([file['Xi'][i], file['Xj'][i]])
        y_elem = array([file['Yi'][i], file['Yj'][i]])
        ax.plot(x_elem, y_elem, linestyle='-', color='black', linewidth=0.5)
        ax.scatter(x_elem, y_elem, color='black', s=6)
    plt.title("File: " + filename.split('/')[-1].split('.eplot')[0] + fig_title, fontsize=7.5)

def save_heat_plot(fig, ax, file, filename, nel, xmax, xmin, ymax, ymin, dx, dy, heat_string, type_heat, nodes_check):
    Smax = file[type_heat].max()
    Smin = file[type_heat].min()
    norm = plt.Normalize(Smin, Smax)
    for i in range(nel):
        x = array([file['Xi'][i], file['Xj'][i]])
        y = array([file['Yi'][i], file['Yj'][i]])
        S = array([file[type_heat][i]])
        lc = coloured_line(x, y, S, fig, ax, norm, 'jet')
        line = ax.add_collection(lc)

    if nodes_check.get() == 1:
        ax.scatter(append(file['Xi'], file['Xj']), append(file['Yi'], file['Yj']), color='black', s=1.5, zorder=2)
    
    plt.colorbar(line, ax=ax, shrink=0.8)
    plt.title("File: " + filename.split('/')[-1].split('.eplot')[0] + heat_string, fontsize=7.5)
    ax.set_xlim(xmin-dx/nel, xmax+dx/nel)
    ax.set_ylim(ymin-dy/nel, ymax+dy/nel)


def HT_diagrams(fig77, ax77, file, filename, figname, figtitle, canvas, colors, Xmax, Xmin, dx, nel, var_type, nodes_check, scale, check_adjustment, parallel_adjust, print_test):

    scale = scale.replace(',','.') if ',' in scale else scale
    scale = float(scale) if scale != '' else 1.0

    if var_type == 'Temp':
        Si = 'Ti'
        Sj = 'Tj'
    elif var_type == 'Qcond':
        Si = 'Qcond'
        Sj = Si
    elif var_type == 'Qconv':
        Si = 'Qconv'
        Sj = Si

    groups = get_element_groups(file,nel,parallel_adjust)
    max_values, min_values, colorr, init_node, end_node, ranges, max_range = get_labels(file,nel,groups,Si,Sj)

    pp = 0
    qq = 0
    rr = 0
    ss = 0

    Ymax1 = file[Si].max() if file[Si].max() > file[Sj].max() else file[Sj].max()
    Ymin1 = file[Si].min() if file[Si].min() < file[Sj].min() else file[Sj].min()
    Ymax2 = file['Yi'].max() if file['Yi'].max() > file['Yj'].max() else file['Yj'].max()
    Ymin2 = file['Yi'].min() if file['Yi'].min() < file['Yj'].min() else file['Yj'].min()

    YTmax = Ymax2
    YTmin = Ymin2
    XTMax = Xmax
    XTMin = Xmin        

    for kkk in groups:        
        for i in kkk:
            x_sin_def = array([file['Xi'][i], file['Xj'][i]])
            y_sin_def = array([file['Yi'][i], file['Yj'][i]])

            L = sqrt((x_sin_def[-1] - x_sin_def[0])**2 + (y_sin_def[-1] - y_sin_def[0])**2)
            lx = (x_sin_def[-1] - x_sin_def[0])/L
            ly = (y_sin_def[-1] - y_sin_def[0])/L

            
            x_i = linspace(0, L, x_sin_def.size)
            if abs(Ymin1) > Ymax1:
                if check_adjustment.get() == 1:
                    y_i = (1/(abs(Ymin1)))*array([file[Si][i], file[Sj][i]])*(max_range.max()/max_range[ranges['group_index'][i]])
                else:
                    y_i = (1/(abs(Ymin1)))*array([file[Si][i], file[Sj][i]])
            elif Ymax1 == 0.0:
                y_i = array([file[Si][i], file[Sj][i]])*(max_range.max()/max_range[ranges['group_index'][i]])
            else:
                if check_adjustment.get() == 1:
                    if max_range[ranges['group_index'][i]] != 0:  
                        y_i = (1/(Ymax1))*array([file[Si][i], file[Sj][i]])*(max_range.max()/max_range[ranges['group_index'][i]])
                    else:
                        y_i = (1/(Ymax1))*array([file[Si][i], file[Sj][i]])
                else:
                    y_i = (1/(Ymax1))*array([file[Si][i], file[Sj][i]])

            x_rot = x_sin_def[0] + (x_i*lx - y_i*ly)
            y_rot = y_sin_def[0] + (x_i*ly + y_i*lx)

            a2 = x_rot - x_sin_def
            b2 = y_rot - y_sin_def

            x_rot = x_sin_def + scale*a2
            y_rot = y_sin_def + scale*b2

            YTmax = y_rot.max() if y_rot.max() > YTmax else YTmax
            YTmin = y_rot.min() if y_rot.min() < YTmin else YTmin

            XTMax = x_rot.max() if x_rot.max() > XTMax else XTMax
            XTMin = x_rot.min() if x_rot.min() < XTMin else XTMin

            xii = array([x_sin_def[0], x_rot[0]])
            yii = array([y_sin_def[0], y_rot[0]])

            xjj = array([x_sin_def[-1], x_rot[-1]])
            yjj = array([y_sin_def[-1], y_rot[-1]])

            ax77.plot(x_sin_def, y_sin_def, linestyle = '-', color = "black", linewidth = 1)
            ax77.plot(x_rot, y_rot, linestyle = '-', color = colorr[i], linewidth = 0.5)
            ax77.fill(append(append(append(xii,x_sin_def),xjj),x_rot[::-1]), append(append(append(yii,y_sin_def),yjj),y_rot[::-1]), color = colorr[i], alpha = 0.1)

            check_repeated_lines(xii,yii,ax77,colorr[i])
            check_repeated_lines(xjj,yjj,ax77,colorr[i])
            
            if nodes_check.get() == 1:
                ax77.scatter(x_sin_def, y_sin_def, color = 'black', s = 1.5)
            
            text_size = 4

            if pp < len(init_node['elem_index']):
                if init_node['elem_index'][pp] == i:
                    ax77.text(x_rot[init_node['node_index'][pp]], y_rot[init_node['node_index'][pp]], 
                    str(around(init_node['value'][pp], 2)), color = colorr[i], size = text_size)
                    pp += 1
            
            if qq < len(end_node['elem_index']):
                if end_node['elem_index'][qq] == i:
                    ax77.text(x_rot[end_node['node_index'][qq]], y_rot[end_node['node_index'][qq]], 
                    str(around(end_node['value'][qq], 2)), color = colorr[i], size = text_size)
                    qq += 1
            
            if len(max_values['elem_index']) > 0:
                if rr < len(max_values['elem_index']):
                    if int(max_values['elem_index'][rr]) == i:
                        ax77.text(x_rot[int(max_values['node_index'][rr])], y_rot[int(max_values['node_index'][rr])], 
                        str(around(max_values['value'][rr], 2)), color = colorr[i], size = text_size)
                        rr += 1
            if len(min_values['elem_index']) > 0:
                if ss < len(min_values['elem_index']):
                    if int(min_values['elem_index'][ss]) == i:
                        ax77.text(x_rot[int(min_values['node_index'][ss])], y_rot[int(min_values['node_index'][ss])], 
                        str(around(min_values['value'][ss], 2)), color = colorr[i], size = text_size)
                        ss += 1


    dy = abs(YTmax - YTmin)
    if dy == 0:
        dy = dx
        
    ax77.set_xlim(XTMin-dx/nel, XTMax+dx/nel)
    ax77.set_ylim(YTmin-dy/nel, YTmax+dy/nel)
    plt.title("File: " + filename.split('/')[-1].split('.eplot')[0] + figtitle, fontsize = 7.5)
    plt.xlabel('X', size=7)
    plt.ylabel('Y', size=7)
    plt.xticks(linspace(Xmin, Xmax, 6), size=6)
    plt.yticks(linspace(Ymin2, Ymax2, 6), size=6)

    if print_test.get() == 1:
        plt.savefig(filename.split('.eplot')[0] + figname + '.png', dpi = 720)

def get_element_groups(file,nel,parallel_adjust):
    tol = 1E-03
    groups = []
    for i in range(nel):
        temporal_group = [i]
        x1 = array([file['Xi'][i], file['Xj'][i]])
        y1= array([file['Yi'][i], file['Yj'][i]])

        checking = False
        checking2 = True
        if (x1[1] - x1[0]) == 0:
            checking = True
            m = x1[0]
        else:
            m = (y1[1] - y1[0])/(x1[1] - x1[0])
        x0 = x1[0]
        y0 = y1[0]
        
        for j in range(nel):
            if i == j:
                pass
            else:
                terminate_loop = False
                for k in groups:
                    if i in k:
                        terminate_loop = True
                        break
                if terminate_loop:
                    checking2 = False
                    break
                else:
                    x1 = array([file['Xi'][j], file['Xj'][j]])
                    y1= array([file['Yi'][j], file['Yj'][j]])

                    if checking:
                        side11 = abs(m - x1[0])
                        side12 = abs(m - x1[1])
                        if side11 < tol and side12 < tol:
                            temporal_group.append(j)
                    else:
                        side11 = y1[0]
                        side12 = m*(x1[0] - x0) + y0
                        
                        side21 = y1[1]
                        side22 = m*(x1[1] - x0) + y0

                        if abs(side11 - side12) < tol and abs(side21 - side22) < tol:
                            if parallel_adjust.get() == 1:
                                test_x1 = ((file['Xi'][i] == file['Xi'][j]) or (file['Xi'][i] == file['Xj'][j]))
                                test_y1 = ((file['Yi'][i] == file['Yi'][j]) or (file['Yi'][i] == file['Yj'][j])) 
                                test_x2 = ((file['Xj'][i] == file['Xi'][j]) or (file['Xj'][i] == file['Xj'][j]))
                                test_y2 = ((file['Yj'][i] == file['Yj'][j]) or (file['Yj'][i] == file['Yj'][j]))
                                if (test_x1 or test_x2) and (test_y1 or test_y2):
                                    temporal_group.append(j)
                            else:
                                temporal_group.append(j)

        
        if len(temporal_group) > 1:
            groups.append(temporal_group)
        elif len(temporal_group) == 1 and checking2:
            groups.append(temporal_group)
        else:
            pass
    
    return groups

def get_labels(file,nell,groups,Si,Sj):
    nel = len(groups)
    color = plt.cm.tab10(linspace(0, 1, nel))
    colores = []
    max_values = DataFrame({'elem_index': Series(dtype = 'int'),'node_index': Series(dtype = 'int'),'value': Series(dtype = 'float')})
    min_values = DataFrame({'elem_index': Series(dtype = 'int'),'node_index': Series(dtype = 'int'),'value': Series(dtype = 'float')})
    init_node = DataFrame({'elem_index':0, 'node_index':0, 'value':0.0} for i in range(nel))
    end_node = DataFrame({'elem_index':0, 'node_index':0, 'value':0.0} for i in range(nel))
    ranges = DataFrame({'local_range':0.0, 'group_index':0} for i in range(nell))
    max_range = zeros(nel)

    for i in range(nel):
        largest_dist = -1E+99
        smallest_dist = 1E+99
        for j in groups[i]:
                
            values = array([file[Si][j], file[Sj][j]])
            x = array([file['Xi'][j], file['Xj'][j]])
            y = array([file['Yi'][j], file['Yj'][j]])
            colores.append(color[i])

            for k in [0,-1]:
                d = sqrt((x[k])**2 + (y[k])**2)
                if d > largest_dist:
                    largest_dist = d
                    end_node.loc[i] = [j,k,values[k]]
                
                if d < smallest_dist:
                    smallest_dist = d
                    init_node.loc[i] = [j,k,values[k]]
    
    del(x)
    del(y)

    for i in range(nel):
        for j in range(1,len(groups[i])-1):
            h = groups[i][j]
            values = values = array([file[Si][h], file[Sj][h]])
            values_1 = array([file[Si][h-1], file[Sj][h-1]])
            values_2 = array([file[Si][h+1], file[Sj][h+1]])

            Vki = values[0]
            Vkj = values[-1]

            if Vki > values_1[0] and Vki > values_2[0]:
                max_values.loc[len(max_values)] = [h,0,Vki]
            elif Vki < values_1[0] and Vki < values[0]:
                min_values.loc[len(min_values)] = [h,0,Vki]

            if Vkj > values_1[-1] and Vkj > values_2[-1]:
                max_values.loc[len(max_values)] = [h,-1,Vkj]
            elif Vkj < values_1[-1] and Vkj < values_2[-1]:
                min_values.loc[len(min_values)] = [h,-1,Vkj]
    
    ii = 0
    for group in groups:
        for i in group:
            values = values = array([file[Si][i], file[Sj][i]])
            local_r = abs(values.max()) if abs(values.max()) > abs(values.min()) else abs(values.min())
            max_range[ii] = local_r if local_r > max_range[ii] else max_range[ii]
            ranges.loc[i] = [local_r,ii]
        ii += 1

    return max_values, min_values, colores, init_node, end_node, ranges, max_range

def get_parallel_elements(file):
    nel = file['Formulacion'].size
    general_groups = []
    for i in range(nel):
        bool_check = False
        if len(general_groups) > 0:
            for k in general_groups:
                if i in k:
                    bool_check = True


        if bool_check:
            pass
        else:
            local_group = [i]
            for j in range(nel):
                if j == i:
                    pass
                else:
                    test_x1 = ((file['Xi'][i] == file['Xi'][j]) or (file['Xi'][i] == file['Xj'][j]))
                    test_y1 = ((file['Yi'][i] == file['Yi'][j]) or (file['Yi'][i] == file['Yj'][j])) 
                    test_x2 = ((file['Xj'][i] == file['Xi'][j]) or (file['Xj'][i] == file['Xj'][j]))
                    test_y2 = ((file['Yj'][i] == file['Yj'][j]) or (file['Yj'][i] == file['Yj'][j]))
                    if (test_x1 and test_x2) and (test_y1 and test_y2):
                        local_group.append(j)
        
        if len(local_group) > 1:
            general_groups.append(local_group)
            local_group = []
    if len(general_groups) > 0:
        list_elems = []
        for group in general_groups:
            n = len(group)
            L = 9E+99
            for i in group:
                L1 = sqrt((file['Xi'][i]-file['Xj'][i])**2 + (file['Yi'][i]-file['Yj'][i])**2)
                L = L1 if L1 < L else L
            l2 = L/(2*n) if n%2 == 0 else L/(n-1)
            l = array([-l2, l2])
            l1 = array([L/4, -L/4]) if n%2 == 0 else array([L/2, -L/2])
            counter = 0
            
            for i in group:
                list_elems.append(i)
                if counter == 2:
                    l1 = l1 + l
                    counter = 0
                    
                l_local = sqrt((file['Xi'][i]-file['Xj'][i])**2 + (file['Yi'][i]-file['Yj'][i])**2)
                ly = (file['Yj'][i]-file['Yi'][i])/l_local
                lx = (file['Xj'][i]-file['Xi'][i])/l_local

                file.loc[i,'Xi'] = file['Xi'][i] - l1[counter]*ly
                file.loc[i,'Xj'] = file['Xj'][i] - l1[counter]*ly

                file.loc[i,'Yi'] = file['Yi'][i] + l1[counter]*lx
                file.loc[i,'Yj'] = file['Yj'][i] + l1[counter]*lx

                counter += 1
    return file, list_elems


