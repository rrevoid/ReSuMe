# -*- coding: utf-8 -*-
"""ReSuMe_LIF_tests.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MNy-GV4znW61corvkmMSgR5TFCOmTvbm
"""

import numpy as np
import matplotlib.pyplot as plt
import random

def poisson_generator(N, dt, nt, rate):
    """
    This function generates Poisson binary spike trains.

    Args:
        pars (dict): dictionary with model parameters
        dt (float): time step
        nt (int): number of time steps
        rate (float): rate of firing

    Returns:
       poisson_train: ndarray of generated Poisson binary spike trains (N x number of times steps)
    """

    # generate uniformly distributed random variables
    u_rand = np.random.rand(N,nt)

    # generate Poisson train
    poisson_train = np.int8(1.*(u_rand < rate*dt/1000.0))

    return poisson_train

def poisson_generator_long(N, dt, nt, rate, len):
    """
    This function generates Poisson binary spike trains.

    Args:
        pars (dict): dictionary with model parameters
        dt (float): time step
        nt (int): number of time steps
        rate (float): rate of firing

    Returns:
       poisson_train: ndarray of generated Poisson binary spike trains (N x number of times steps)
    """

    # generate uniformly distributed random variables
    u_rand = np.random.rand(N,nt)

    # generate Poisson train
    poisson_train = np.int8(1.*(u_rand < rate*dt/1000.0))[0]
    k=0
    print(k,nt)
    while(k<nt):
      print('a')
      if(poisson_train[k]):
        poisson_train[k:k+len]=1
        print('found 1')
        k+=len
      else:
        k+=1
        print('found 0')
    return poisson_train

a=np.zeros(10)
a[5:8]=1
a

dt=0.1
tmax=400
nt=int(tmax/dt)+1
rate=50
t = np.linspace(0.0, tmax, nt)
S_in=poisson_generator(1, dt, nt, rate).reshape(t.shape)

plt.plot(t, S_in)

S_in2 = poisson_generator_long(1, dt, nt, rate, 10)

plt.plot(S_in2[500:1000])

print(S_in2)

"""LIF network"""

from tqdm import tqdm

N = 800 # total number of neurons

N=800
neur_ei=np.ones(N)
N_in=int(0.2*N)
inh_inds=np.array(random.sample(range(0,800),N_in))
neur_ei[inh_inds]=0
ex_inds=np.where(neur_ei>0)

De = 5. # std for the stochastic current for excitatory neurons
Di = 2. # std for the stochastic current for inhibitory neurons

# LIF model parameters
p = {}
# membrane capacitance:
p['tau'] = 30. # (ms)
# membrane resistance:
p['R'] = 1 # (GOhm)
# membrane potential threshold:
p['V_t'] = 15.   # (mV)
# reversal potential of the leakage current
p['E_L'] = 13.5  # (mV)
# membrane reset voltage:
p['V_r'] = 13.5   # (mV)
p['t_r_e'] = 3. # (ms)
p['t_r_i'] = 2. # (ms)

# injected current (nA)
I0 = 13.5

C_ee=0.3
C_ei=0.2
C_ie=0.4
C_ii=0.1

def LIF_network(N,dt,tmax,p,W,I0,S_in, neur_ei, D):
    """
    This function implements a simple network of LIF neurons

    Args:
        N (int): total number of neurons
        dt (float): time step (ms)
        tmax (float): final time (ms)
        p (dict): parameters of the LIF model
        W (numpy ndarray): matrix of the synaptic weights
        I0 (float): injected current (pA)
        D (float, optional): coefficient to transform from input signal to
        external current.
        S_in - input signal (sequence of 0 and 1)
    Returns:
        V, spikes: calculated membrane potentials and binary spike trains
    """

    # initialization
    nt = int(tmax/dt) + 1
    spikes = np.zeros((nt,N)) # binary spike train
    V = np.zeros((nt,N)) # membrane potentials

    # parameters of the LIF model
    tau = p['tau']

    # initial conditions for membrane potentials
    V[0,:] = p['E_L']
    # refractory time counter
    counter = np.zeros((N, 2))
    counter[:,1]=neur_ei

    # time loop
    for it in tqdm(range(nt-1)):

        # generate the external current
        I_ext = I0 + D*S_in[it]
        # calculate the synaptic current
        I_syn = W @ spikes[it,:].reshape([N,1])
        # get the total current
        IC = I_ext + I_syn
        IC = IC.reshape([N,])

        # get all neurons that should be kept contant
        # during the refraction period
        iref = np.where(counter[:,0]>0)
        idyn = np.where(counter[:,0]==0)

        # update the membrane potentials using the Euler scheme
        V[it+1,idyn] = V[it,idyn] + dt/tau*(p['E_L'] - V[it,idyn] + p['R']*IC[idyn])

        # refractored membranes are kept at the reset potential value
        V[it+1,iref] = p['V_r']
        counter[iref,0] -= 1

        # correct the potentials below the reset value
        ireset = np.where(V[it+1,:] < p['V_r'])
        V[it+1,ireset] = p['V_r']


        # check all fired neurons on this time step
        ifired = np.where(V[it+1,:] >= p['V_t'])
        if(len(ifired[0])>0):
          #print('fire',V[it+1,ifired], it+1)
          V[it+1,ifired] = p['V_r']
          # update spike train
          spikes[it+1,ifired] += 1.0
          # update refractory counter for all fired neurons
          for g in ifired[0]:

            if(counter[g,1]):
              counter[g,0] += int(p['t_r_e']/dt)
            else:
              counter[g,0] += int(p['t_r_i']/dt)


    print()
    return V, spikes

def D(a,b):
  r = a-b
  return np.sqrt(np.sum(r**2))

def probability(C, dist, lmb=2):
  power = -(dist**2)/(lmb**2)
  return C*np.exp(power)

def geom_matrix(N, size_x, size_y, size_z):
  coords = np.zeros((N,3))
  z=0
  for k in range(N):
    coords[k,0]=k%size_x
    coords[k,1]=(k//size_y)%size_y
    coords[k,2]=z
    if(coords[k,1]==size_y-1)and(coords[k,0]==size_x-1):
      z+=1
  return coords

def get_W(C_ee, C_ei, C_ie, C_ii, neur_ei, weight):
  distmat=geom_matrix(N, 10, 10, 8)
  W=np.zeros((N,N))
  prob=np.zeros((N,N))
  for a in range(N):
    for b in range(N):
      if(neur_ei[a])and(neur_ei[b]):
        C=C_ee
      elif(neur_ei[a])and(not neur_ei[b]):
        C=C_ei
      elif(not neur_ei[a])and(neur_ei[b]):
        C=C_ie
      else:
        C=C_ii
      dist=D(distmat[a], distmat[b])
      prob[a,b]=probability(C, dist)

  W = weight*(np.random.random(size=(N,N))<prob)
  #W=weight*prob
  return W

def raster_plot(spikes,t):
    """
    This function visualize an average activity of
    the neuron network and its spike train raster plot

    Args:
        spikes (numpy ndarray): binary spike trains for all neurons
        t (numpy array ): time array in ms
    """

    fig, ax = plt.subplots(1,2,figsize=(16,4))

    A = np.mean(spikes, axis = 1)
    ax[0].plot(t, A, color = 'tab:blue', linewidth = 2.)
    ax[0].set_xlabel(r'$t$ [ms]', fontsize = 16)
    ax[0].set_ylabel(r'$A$', fontsize = 16)


    N = spikes.shape[1]
    i = 0
    while i < N:
        if spikes[:,i].sum() > 0.:
            t_sp = t[spikes[:,i] > 0.5]  # spike times
            ax[1].plot(t_sp, i * np.ones(len(t_sp)), 'k|', ms=1., markeredgewidth=2)
        i += 1
    plt.xlim([t[0], t[-1]])
    plt.ylim([-0.5, N + 0.5])
    ax[1].set_xlabel(r'$t$ [ms]', fontsize = 16)
    ax[1].set_ylabel(r'# neuron', fontsize = 16)

    plt.show()

p['R'] = 1

W = get_W(C_ee, C_ei, C_ie, C_ii, neur_ei, 1)

V, spikes = LIF_network(N,dt,tmax,p,W,I0,S_in2, neur_ei, 20)

raster_plot(spikes,t)

plt.plot(t, S_in)

A = np.mean(spikes, axis = 1)
plt.plot(t,A)
plt.xlim(380,400)

plt.plot(t,V[:,2])
plt.plot(t,V[:,-1])
plt.ylim(ymin=13.4)
plt.plot(t, S_in*15)
plt.xlim(0,50)

spikes[:,1]

len(np.where(W>0)[0])