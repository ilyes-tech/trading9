import math
import numpy as np

SUPPORTED_PRIMITIVES={
    "NOT","XOR","XNOR","NAND","NOR",
    "EXACT_K_OF_N","AT_MOST_K_OF_N","MAJORITY","SUPERMAJORITY","UNANIMOUS",
    "EDGE_RISING","EDGE_FALLING","PERSIST_N","RECENT_WITHIN_N",
    "THEN_WITHIN_N","THREE_STAGE_WITHIN_N"
}

def _mask(x,n=None,label="MASK"):
    a=np.asarray(x,dtype=bool)
    if a.ndim!=1:
        raise ValueError("BAD_MASK_DIM:"+label)
    if n is not None and a.shape!=(int(n),):
        raise ValueError("BAD_MASK_SHAPE:"+label)
    return a

def _matrix(masks):
    if not isinstance(masks,(list,tuple)) or not masks:
        raise ValueError("NO_MASKS")
    xs=[_mask(x,label="CHILD") for x in masks]
    n=len(xs[0])
    if any(len(x)!=n for x in xs):
        raise ValueError("MASK_LENGTH_MISMATCH")
    return np.asarray(xs,dtype=bool)

def _segments(time,sec):
    t=np.asarray(time,dtype=np.int64)
    if t.ndim!=1:
        raise ValueError("BAD_TIME_DIM")
    if len(t)==0:
        return []
    s=int(sec)
    if s<=0:
        raise ValueError("BAD_SEC")
    cuts=np.flatnonzero(np.diff(t)!=s)+1
    starts=np.r_[0,cuts]
    ends=np.r_[cuts,len(t)]
    return [(int(a),int(b)) for a,b in zip(starts,ends)]

def boolean_not(mask):
    return ~_mask(mask)

def xor_masks(masks):
    a=_matrix(masks)
    return (np.sum(a,axis=0)%2)==1

def xnor_masks(masks):
    return ~xor_masks(masks)

def nand_masks(masks):
    return ~np.all(_matrix(masks),axis=0)

def nor_masks(masks):
    return ~np.any(_matrix(masks),axis=0)

def exact_k_of_n(masks,k):
    a=_matrix(masks)
    k=int(k)
    if not 0<=k<=a.shape[0]:
        raise ValueError("BAD_K")
    return np.sum(a,axis=0)==k

def at_most_k_of_n(masks,k):
    a=_matrix(masks)
    k=int(k)
    if not 0<=k<=a.shape[0]:
        raise ValueError("BAD_K")
    return np.sum(a,axis=0)<=k

def majority(masks):
    a=_matrix(masks)
    k=a.shape[0]//2+1
    return np.sum(a,axis=0)>=k

def supermajority(masks):
    a=_matrix(masks)
    k=int(math.ceil((2.0*a.shape[0])/3.0))
    return np.sum(a,axis=0)>=k

def unanimous(masks):
    return np.all(_matrix(masks),axis=0)

def edge_rising(mask,time,sec):
    x=_mask(mask)
    t=np.asarray(time,dtype=np.int64)
    if len(x)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    out=np.zeros(len(x),dtype=bool)
    for a,b in _segments(t,sec):
        if b-a>=2:
            out[a+1:b]=(~x[a:b-1])&x[a+1:b]
    return out

def edge_falling(mask,time,sec):
    x=_mask(mask)
    t=np.asarray(time,dtype=np.int64)
    if len(x)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    out=np.zeros(len(x),dtype=bool)
    for a,b in _segments(t,sec):
        if b-a>=2:
            out[a+1:b]=x[a:b-1]&(~x[a+1:b])
    return out

def persist_n(mask,time,sec,n):
    x=_mask(mask)
    t=np.asarray(time,dtype=np.int64)
    if len(x)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    n=int(n)
    if n<1:
        raise ValueError("BAD_N")
    if n==1:
        return x.copy()
    out=np.zeros(len(x),dtype=bool)
    for a,b in _segments(t,sec):
        run=0
        for i in range(a,b):
            run=run+1 if x[i] else 0
            if run>=n:
                out[i]=True
    return out

def recent_within_n(mask,time,sec,n):
    x=_mask(mask)
    t=np.asarray(time,dtype=np.int64)
    if len(x)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    n=int(n)
    if n<1:
        raise ValueError("BAD_N")
    out=np.zeros(len(x),dtype=bool)
    for a,b in _segments(t,sec):
        last=-10**18
        for i in range(a,b):
            if x[i]:
                last=i
            if i-last<n:
                out[i]=True
    return out

def then_within_n(a_mask,b_mask,time,sec,n):
    a=_mask(a_mask)
    b=_mask(b_mask,len(a),"B")
    t=np.asarray(time,dtype=np.int64)
    if len(a)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    n=int(n)
    if n<1:
        raise ValueError("BAD_N")
    out=np.zeros(len(a),dtype=bool)
    for s,e in _segments(t,sec):
        last_a=-10**18
        for i in range(s,e):
            if b[i] and 1<=i-last_a<=n:
                out[i]=True
            if a[i]:
                last_a=i
    return out

def three_stage_within_n(a_mask,b_mask,c_mask,time,sec,n_ab,n_bc):
    a=_mask(a_mask)
    b=_mask(b_mask,len(a),"B")
    c=_mask(c_mask,len(a),"C")
    t=np.asarray(time,dtype=np.int64)
    if len(a)!=len(t):
        raise ValueError("TIME_MASK_LENGTH_MISMATCH")
    n_ab=int(n_ab); n_bc=int(n_bc)
    if n_ab<1 or n_bc<1:
        raise ValueError("BAD_N")
    stage_b=then_within_n(a,b,t,sec,n_ab)
    return then_within_n(stage_b,c,t,sec,n_bc)

def self_check():
    t=np.array([0,60,120,180,600,660,720,780],dtype=np.int64)
    a=np.array([0,1,1,0,1,1,0,0],dtype=bool)
    b=np.array([0,0,1,1,0,1,1,0],dtype=bool)
    c=np.array([0,0,0,1,0,0,1,1],dtype=bool)
    assert np.array_equal(edge_rising(a,t,60),np.array([0,1,0,0,0,0,0,0],dtype=bool))
    assert np.array_equal(edge_falling(a,t,60),np.array([0,0,0,1,0,0,1,0],dtype=bool))
    assert np.array_equal(persist_n(a,t,60,2),np.array([0,0,1,0,0,1,0,0],dtype=bool))
    assert np.array_equal(recent_within_n(a,t,60,2),np.array([0,1,1,1,1,1,1,0],dtype=bool))
    assert np.array_equal(then_within_n(a,b,t,60,2),np.array([0,0,1,1,0,1,1,0],dtype=bool))
    cross=then_within_n(np.array([0,0,0,1,0,0,0,0],dtype=bool),np.array([0,0,0,0,1,0,0,0],dtype=bool),t,60,2)
    assert not bool(cross[4])
    assert np.array_equal(three_stage_within_n(a,b,c,t,60,2,2),np.array([0,0,0,1,0,0,1,1],dtype=bool))
    x=np.array([1,0,1],dtype=bool); y=np.array([1,1,0],dtype=bool)
    assert np.array_equal(xor_masks([x,y]),np.array([0,1,1],dtype=bool))
    assert np.array_equal(exact_k_of_n([x,y],1),np.array([0,1,1],dtype=bool))
    assert np.array_equal(majority([x,y]),np.array([1,0,0],dtype=bool))
    assert np.array_equal(supermajority([x,y]),np.array([1,0,0],dtype=bool))
    assert np.array_equal(unanimous([x,y]),np.array([1,0,0],dtype=bool))
    print("V57_V433_LOGIC_KERNEL_V1_SELF_CHECK=PASS|PRIMITIVES=%d|SEGMENT_AWARE=PASS|STRICT_MAJORITY=PASS|ORDERS=DISABLED"%len(SUPPORTED_PRIMITIVES))

if __name__=="__main__":
    self_check()
