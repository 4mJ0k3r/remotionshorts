"""Deterministic swing/stance foot planning and connected two-bone knees.

The plan is precomputed from the root trajectory, so scrubbing and chunked
renders produce the same planted feet. A stance never inherits root motion.
"""
import math


def add(a,b):
    return tuple(x+y for x,y in zip(a,b))


def subtract(a,b):
    return tuple(x-y for x,y in zip(a,b))


def scale(vector,value):
    return tuple(component*value for component in vector)


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def normalized(vector,fallback=(0,-1,0)):
    length=math.sqrt(dot(vector,vector))
    return scale(vector,1/length) if length>1e-8 else fallback


def blend(a,b,weight):
    return add(scale(a,1-weight),scale(b,weight))


def knee_of(hip,ankle,pole,length_a,length_b):
    delta=subtract(ankle,hip)
    distance=math.sqrt(dot(delta,delta))
    axis=normalized(delta,(0,0,-1))
    # Keep the explicit ankle target even for legacy extreme camera poses.
    stretch=max(1,(distance+.0001)/(length_a+length_b))
    length_a*=stretch
    length_b*=stretch
    distance=max(.0001,distance)
    along=(length_a**2-length_b**2+distance**2)/(2*distance)
    height=math.sqrt(max(0,length_a**2-along**2))
    perpendicular=subtract(pole,scale(axis,dot(pole,axis)))
    return add(add(hip,scale(axis,along)),scale(normalized(perpendicular),height))


class FootStepper:
    def __init__(self,root_at,windows,size=1,yaw_at=None,step_speed=.45,step_dir=(0,1),frames=2145):
        self.root_at=root_at
        self.windows=list(windows)
        self.step_dir=tuple(step_dir)
        self.size=size
        self.yaw_at=yaw_at or (lambda frame:0)
        self.samples={}
        self.frames=frames
        self.nominal_speed=step_speed
        foot_yaw=[self.yaw_at(1)]*2
        feet=[self.neutral(1,index) for index in range(2)]
        windows={start:(end,weight) for start,end,weight in self.windows}
        frame=1
        while frame<=frames:
            if frame not in windows:
                self.samples[frame]=self.sample(feet,foot_yaw)
                frame+=1
                continue
            start=frame
            end,weight=windows[start]
            duration=end-start
            half_steps=max(2,math.ceil(duration*step_speed/math.pi))
            if half_steps%2:
                half_steps+=1
            half_duration=duration/half_steps
            direction=subtract(tuple(root_at(end)),tuple(root_at(start)))
            moving=math.hypot(direction[0],direction[1])>.001
            fallback=normalized((step_dir[0],step_dir[1],0))
            direction=normalized((direction[0],direction[1],0),fallback)
            previous_index=-1
            swing_start=None
            swing_target=None
            yaw_start=0
            yaw_target=0
            for frame in range(start,end+1):
                elapsed=(frame-start)/half_duration
                index=min(half_steps-1,int(elapsed))
                progress=1 if frame==end else elapsed-index
                swinging=index%2
                if index!=previous_index:
                    if previous_index>=0:
                        old=previous_index%2
                        feet[old]=swing_target
                        foot_yaw[old]=yaw_target
                    swing_start=feet[swinging]
                    yaw_start=foot_yaw[swinging]
                    landing=start+(index+1)*half_duration
                    predicted=min(end,landing+half_duration*.5)
                    if index>=half_steps-2:
                        predicted=end
                    swing_target=self.neutral(predicted,swinging)
                    yaw_target=self.yaw_at(predicted)
                    if not moving and index<half_steps-2:
                        stride=.13*weight*(1 if (index//2)%2==0 else -1)
                        swing_target=add(swing_target,scale(direction,stride))
                    previous_index=index
                smooth=.5-.5*math.cos(math.pi*progress)
                lift=.11*weight*math.sin(math.pi*progress)
                feet[swinging]=add(blend(swing_start,swing_target,smooth),(0,0,lift))
                if abs(yaw_target-yaw_start)>.01:
                    mid_yaw=(yaw_start+yaw_target)*.5
                    side=-1 if swinging==0 else 1
                    arc=(math.cos(mid_yaw)*side,math.sin(mid_yaw)*side,0)
                    feet[swinging]=add(feet[swinging],scale(arc,.04*math.sin(math.pi*progress)))
                foot_yaw[swinging]=yaw_start+(yaw_target-yaw_start)*smooth
                phase=index*math.pi+progress*math.pi
                bob=.025*weight*math.sin(2*phase)
                state=self.sample(feet,foot_yaw)
                state.update(active=True,lift=tuple(lift if side==swinging else 0 for side in range(2)),bob=bob,arm_swing=math.sin(math.radians(18))*math.sin(phase)*weight,direction=direction)
                self.samples[frame]=state
            feet=[self.neutral(end,index) for index in range(2)]
            foot_yaw=[self.yaw_at(end)]*2
            self.samples[end]=self.sample(feet,foot_yaw)
            frame=end+1

    def neutral(self,frame,index):
        x,y,z=self.root_at(frame)
        yaw=self.yaw_at(frame)
        sideways=(-1 if index==0 else 1)*.13*self.size
        forward=-.09
        return (x+sideways*math.cos(yaw)-forward*math.sin(yaw),y+sideways*math.sin(yaw)+forward*math.cos(yaw),z+.055*self.size)

    @staticmethod
    def sample(feet,yaws):
        return {'feet':tuple(tuple(foot) for foot in feet),'yaw':tuple(yaws),'lift':(0,0),'bob':0,'arm_swing':0,'active':False,'direction':(0,1,0)}

    def at(self,frame):
        return self.samples[max(1,min(self.frames,int(frame)))]
