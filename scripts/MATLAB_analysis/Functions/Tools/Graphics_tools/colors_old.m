function [COLORS,COLORS_DARK,COLORS_LIGHT,COLORS_RGB,COLORS_DARK_RGB,COLORS_LIGHT_RGB] = colors

COLORS = {'#0072bd','#d95319','#77ac30','#edb120','#7e2f8e',...
    '#0072bd','#d95319','#77ac30','#edb120','#7e2f8e',...
    '#0072bd','#d95319','#77ac30','#edb120','#7e2f8e'};

COLORS_DARK = {'#253597','#9f2513','#186114','#b08315','#4f0d5c',...
    '#253597','#9f2513','#186114','#b08315','#4f0d5c',...
    '#253597','#9f2513','#186114','#b08315','#4f0d5c'};

COLORS_LIGHT = {'#48b2f7','#ff814a','#b6e677','#f7ca5c','#c05fd4',...
    '#48b2f7','#ff814a','#b6e677','#f7ca5c','#c05fd4',...
    '#48b2f7','#ff814a','#b6e677','#f7ca5c','#c05fd4'};

for i = 1:length(COLORS)
    COLORS_RGB{i} = sscanf(COLORS{i}(2:end),'%2x%2x%2x',[1 3])/255;
    COLORS_DARK_RGB{i} = sscanf(COLORS_DARK{i}(2:end),'%2x%2x%2x',[1 3])/255;
    COLORS_LIGHT_RGB{i} = sscanf(COLORS_LIGHT{i}(2:end),'%2x%2x%2x',[1 3])/255;
end

end
