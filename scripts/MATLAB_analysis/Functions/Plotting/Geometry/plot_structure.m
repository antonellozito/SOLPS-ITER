function h = plot_structure(structure,varargin)
%
% Routine to plot structure (vessel, templates, ...).
% 
% Input arguments:
%
% - structure : struct containing r and z coordinates of the structure
% - options   : list of plot options compatible with Matlab plot command
%
%
% Output arguments:
%
% - h   : column vector of handles to the different parts of the structure
%
% TODO: adapt in case of arbitrary number of substructures

% Check current status of hold
hs = ishold;

% Plot individual segments
h = zeros(length(structure)-1,1);
for i = 1:length(structure)-1
    h(i) = plot(structure(i).r,structure(i).z,varargin{:}); hold on;
end

% Fill individual components
for i = 1:size(structure,2)
    if min(structure(i).z) < -1.3
        fillout(structure(i).r,structure(i).z,[0.75 3 -1.504 1.504],[1 1 1]); hold on;
    else
        fill(structure(i).r,structure(i).z,[0.88 0.88 0.88]); hold on;
    end
end

% Plot outer vessel contour again
for i = 1:length(structure)-1
    if min(structure(i).z) < -1.3
        h(i) = plot(structure(i).r,structure(i).z,varargin{:}); hold on;
    end
end

% Reset status of hold
if ~hs, hold off;

end

end


function h=fillout(x,y,lims,varargin)

h=[];

if nargin <2
  disp(['## ',mfilename,' : more input arguments required']);
  return
end
 
if prod(size(x)) > length(x)
  x=var_border(x);
end
if prod(size(y)) > length(y)
  y=var_border(y);
end

if length(x) ~= length(y)
  disp(['## ',mfilename,' : x and y must have the same size']);
  return  
end

if nargin<4
  varargin={'g'};  
end
if nargin<3
  lims=[min(x) max(x) min(y) max(y)];
else
  if lims(1) > min(x), lims(1)=min(x); end
  if lims(2) < max(x), lims(2)=max(x); end
  if lims(3) > min(y), lims(3)=min(y); end
  if lims(4) < max(y), lims(4)=max(y); end 
end

xi=lims(1); xe=lims(2);
yi=lims(3); ye=lims(4);

j=find(x==min(x)); j=j(1);

x=x(:);
y=y(:);
x=[x(j:end)' x(1:j-1)' x(j)];
y=[y(j:end)' y(1:j-1)' y(j)];

x=[xi   xi xe xe xi xi   x(1) x];
y=[y(1) ye ye yi yi y(1) y(1) y];

h=fill(x,y,varargin{:});
set(h,'edgecolor','none');

function [x,xc] = var_border(M)

x  = [];
xc = [];

if nargin == 0
  disp('» no variable')
  return
end

xl = M(:,1);
xt = M(end,:);  xt = xt';
xr = M(:,end);  xr = flipud(xr);
xb = M(1,:);    xb = flipud(xb');

x =  [xl; xt; xr; xb];

xc =  [xl(1) xl(end) xr(1) xr(end)];

end

end