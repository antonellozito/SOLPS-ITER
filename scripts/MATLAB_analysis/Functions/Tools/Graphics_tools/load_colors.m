function output = load_colors(type,number,def)

% Syntax : colors(type,number,def)
%
%  type:      type of colormap
%             the options are:
%             - 'default': default matlab colors
%             - 'default_dark': default matlab colors (darker version)
%             - 'default_light': default matlab colors (lighter version)
%             - 'parula'
%             - 'turbo'
%             - 'hot'
%             - 'cool'
%             - 'spring'
%             - 'summer'
%             - 'autumn'
%             - 'winter'
%             - 'grey'
%
%  number:    number of colors to be picked
%
%  def:       type of color definition ('rgb' or 'hex')
%  

default = {[0.0000, 0.4470, 0.7410], [0.8500, 0.3250, 0.0980], [0.9290, 0.6940, 0.1250], ...
    [0.4940, 0.1840, 0.5560], [0.4660, 0.6740, 0.1880], [0.3010, 0.7450, 0.9330], [0.6350, 0.0780, 0.1840]};

default_dark = {[0.1451, 0.2078, 0.5922], [0.6235, 0.1451, 0.0745], [0.6902, 0.5137, 0.0824], ...
    [0.3098, 0.0510, 0.3608], [0.0941, 0.3804, 0.0784], [0.3059, 0.4902, 0.5686], [0.3412, 0.0549, 0.1098]};

default_light = {[0.2824, 0.6980, 0.9686], [1.0000, 0.5059, 0.2902], [0.9686, 0.7922, 0.3608], ...
    [0.7529, 0.3725, 0.8314], [0.7137, 0.9020, 0.4667], [0.5647, 0.8627, 0.9882], [0.9216, 0.4510, 0.5373]};

if strcmp(type,'default') || strcmp(type,'default_dark') ||strcmp(type,'default_light')

    if number <= 7

        for i = 1:number
            eval(sprintf('output{%d} = %s{%d};',i,type,i));
        end

    else

        for i = 1:7
            eval(sprintf('output{%d} = %s{%d};',i,type,i));
        end
        for i = 8:number
            k = floor(i/7)-1;
            if mod(i,7)==0
                k = k-1;
            end
            eval(sprintf('output{%d} = %s{%d};',i,type,i-7-7*k));
        end

    end

else

    eval(sprintf('temp = %s(%d);',type,number));

    for i = 1:number
        output{i} = temp(i,:);
    end

end

switch def

    case 'rgb'

        output = output;

    case 'hex'

        for i = 1:number
            output{i} = rgb2hex(output{i});
        end

end

end
