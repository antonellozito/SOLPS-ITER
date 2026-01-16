function out=intersects(p1,q1,p2,q2)

      o1 = orient(p1, q1, p2);
      o2 = orient(p1, q1, q2);
      o3 = orient(p2, q2, p1);
      o4 = orient(p2, q2, q1);
      
      out = 1 ;

      if (o1 ~= o2 && o3 ~= o4) 
          return
      end
  
      if (o1 == 0 && onSegment(p1, p2, q1)) 
          return
      end
  
      if (o2 == 0 && onSegment(p1, q2, q1)) 
          return
      end
  
      if (o3 == 0 && onSegment(p2, p1, q2)) 
          return 
      end
  
      if (o4 == 0 && onSegment(p2, q1, q2)) 
          return 
      end
      out = 0;
          
end


function out=onSegment(p, q, r)

out = 0;
if ( (q(1) <= max(p(1), r(1))) && (q(1) >= min(p(1), r(1))) && (q(2) <= max(p(2), r(2))) &&  (q(2) >= min(p(2), r(2))) )
    out = 1;
end
return
end


function out=orient(p, q, r)

val = (q(2) - p(2)) * (r(1) - q(1)) - (q(1) - p(1)) * (r(2) - q(2));

if (val > 0) 
out = 1;
return
else
	if (val < 0)
    out = 2;
    return
else
    out = 0;
    return
end
end
end
