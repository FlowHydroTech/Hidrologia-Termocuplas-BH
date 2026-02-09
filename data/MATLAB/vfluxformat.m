function [output]=vfluxformat(varargin)
%
% VFLUXFormat - Formats and synchronizes temperature time series data
%   from multiple sensors in a depth profile.
%
% Description:
%   Copies temperature time series data from multiple sensors, stored in
%   column vectors, to a MATLAB structure format that can be
%   processed with the VFLUX program.
%
%   If all sensors were sampled at the same times, VFLUXFormat simply
%   copies the data to the new format.
%
%   If different sensors were sampled at different times, VFLUXFormat
%   resamples all input time series to the "lowest common denominator",
%   that is, it trims all the input series to the shortest time range that
%   is common to all the input series, and interpolates/resamples the input
%   series to have the lowest sampling rate of all the input series.
%   Interpolation is performed with the MATLAB function 'interp1', using
%   the linear method.
%
% Usage:
%   output = vfluxformat(time, temp, depth)
%   output = vfluxformat(time, [tempA tempB ...], depth)
%   output = vfluxformat(time1, temp1, depth1, time2, temp2, depth2, ...)
%   output = vfluxformat(time1, [temp1A temp1B ...],, depth1, time2, [temp2A temp2B ...], depth2, ...)
%
% Input:
%   time (or time1, etc.) = a column vector of sample times in days.
%       Sampling times must be monotonic and evenly-spaced throughout, with
%       no gaps in sampling.
%   temp (or temp1, etc.) = a column vector of temperatures in degrees
%       Celcius that correspond to the times in 'time', with same length as
%       'time'; or a matrix of more than one column, like [tempA tempB
%       ...], where each column is data from a separate sensor, all of the
%       same length as time1.
%   depth (or depth1, etc.) = a row vector or scalar of depth position(s)
%       in meters for each of the sensors in 'temp', where each column
%       represents one sensor.  The 'depth' vector must have the same
%       number of columns as the associated 'temp' matrix.
%   time2 = a column vector of sample times that are different than time1.
%   ...etc.
%
% NOTE: It is necessary that the order of temp columns be in order of
% increasing sensor depth, throughout all the input matrices (for example,
% temp2B must be deeper than temp2A must be deeper than temp1B, etc.), so
% that the depth vector is monotonically increasing. This requirement may
% be relaxed in a future version.
%
% Output:
%   output = a MATLAB structure containing three arrays:
%     output.time = a column vector of sample times in days.
%     output.temp = a matrix of temperatures in degrees Celcius, where each
%         column is data from a separate sensor, all of the same length as
%         'output.time'.
%     output.depth = a row vector of depth positions in meters for each of
%         the sensors in 'output.temp', where each column represents one
%         sensor.  The 'output.depth' vector has the same number of columns
%         as 'output.temp'. 
%
% Example:
%   profile01 = vfluxformat(time01, [temp0105 temp0110 temp0115], [0.05 0.1 0.15])
%  [  output  = vfluxformat( time,              temp,                   depth)    ]

% Written by Ryan Gordon, Syracuse University, January 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 107, updated 8/29/2011

% Error check input
if nargin<3 %if fewer than 3 arguments
    error('Must supply at least three input arguments: one time vector, one temp vector, and one depth.')
elseif mod(nargin,3)~=0 %if number of arguments is not divisible by 3
    error('Wrong number of inputs--each time vector must have at least one associated temp vector and one associated depth value.')
end %if
for argcount=1:3:nargin %go through all the time vectors
    timenum=argcount/3+2/3;
    Ps=(varargin{argcount}(end)-varargin{argcount}(1))/(length(varargin{argcount})-1); %sampling period (in days)
    if size(varargin{argcount},2)>1 || size(varargin{argcount},1)<2 %if time input has >1 columns or <2 rows
        error('time%d is not a column vector.',timenum)
    elseif size(varargin{argcount},1)~=size(varargin{argcount+1},1) %if time and temp inputs are not the same length
        error('time%d and temp%d are not the same length.',timenum,timenum)
    elseif size(varargin{argcount+2},1)>1 %if depth input has >1 rows
        error('depth%d is not a scalar or row vector.',timenum)
    elseif size(varargin{argcount+1},2)~=size(varargin{argcount+2},2) %if temp and depth inputs don't have the same number of columns
        error('temp%d and depth%d do not have the same number of columns.',timenum,timenum)
    elseif any(diff(varargin{argcount})<=0) %if time is not monotonically increasing
        error('time%d is not monotonically increasing.',timenum)
    end %if
    if abs(max(diff(varargin{argcount}))-min(diff(varargin{argcount})))>0.25*Ps  %if time is not evenly spaced (any spacing varies by > 1/4 of sampling period)
        display(sprintf('Warning: time%d is not evenly spaced throughout.',timenum))
        disp('Press any key to continue.')
        pause
    end %if
end %for

disp('Beginning format . . .')

% Calculate time series stats in 'info' matrix
maxtimenum=nargin/3;
info(1:maxtimenum,4)=NaN; %preallocate info matrix
totaltemps=0; %create totaltemps counter variable
for argcount=1:3:nargin %go through all the time vectors
    timenum=argcount/3+2/3;
    Ps=(varargin{argcount}(end)-varargin{argcount}(1))/(length(varargin{argcount})-1); %sampling period (in days) of timeTIMENUM
    info(timenum,1)=varargin{argcount}(1); %start of timeTIMENUM
    info(timenum,2)=varargin{argcount}(end); %end of timeTIMENUM
    info(timenum,3)=1/Ps; %sampling rate (samples per day) of timeTIMENUM
    info(timenum,4)=length(varargin{argcount}); %number of samples (length of timeTIMENUM)
    tempnum=size(varargin{argcount+1},2); %collects number of temp columns (for preallocation below)
    totaltemps=totaltemps+tempnum; %sums total number of temp columns (for preallocation below)
end %for

% If time series are all the same (start and end times are all within 1/4 of sampling period [doesnt matter which one, so use last one stored in Ps]),
% and number of samples are all the same), then . . .
if abs(max(info(:,1))-min(info(:,1)))<0.25*Ps && abs(max(info(:,2))-min(info(:,2)))<0.25*Ps && max(info(:,4))-min(info(:,4))<0.1
    
    % Write output.time vector equal to time1
    output.time=varargin{1};
    
    % Concatenate all temp vectors in output.temp matrix
    output.temp=[]; %create blank output.temp variable
    for argcount=2:3:nargin %go through all the temp vectors
        output.temp=horzcat(output.temp,varargin{argcount}); %append temp to output.temp matrix
    end %for
    
    disp('Note: All sensors were sampled at the same times:')
    disp('      No interpolation was necessary. This is good.')

% If time series are not all the same, then . . .
else
    
    % Create new time vector ('newtime') that spans the shortest common time range, with the lowest sampling rate, of all the input time series
    maxstart=max(info(:,1)); %latest start time of all time series
    minend=min(info(:,2)); %earliest end time of all time series
    minrate=min(info(:,3)); %lowest sampling rate of all time series
    maxperiod=1/minrate; %max sampling period (in days) of all the time series (inverse of min sampling rate)
    newtime=(maxstart:maxperiod:minend)'; %newtime vector (Note: (X)' is the transpose operator, to make result a column instead of row)
    output.time=newtime; %write output.time vector equal to newtime
    
    % Preallocate output.temp matrix
    output.temp(1:length(newtime),1:totaltemps)=NaN;
    
    % Resample/interpolate time series based on newtime
    totaltemps=0; %reset totaltemps counter variable
    for argcount=1:3:nargin %go through all the time vectors
        time=varargin{argcount}; %make time vector, for simplicity of coding
        temp=varargin{argcount+1}; %make temp matrix, for simplicity of coding
        tempnum=size(varargin{argcount+1},2); %collects number of temp columns
        totaltemps=totaltemps+tempnum; %sums total number of temp columns
        
        % Use ONLY ONE of following interpolation methods:
        newtemp=interp1(time,temp,newtime,'linear'); %interpolation using linear method
        %newtemp=interp1(time,temp,newtime,'spline'); %interpolation using cubic spline method
        %newtemp=interp1(time,temp,newtime,'pchip'); %interpolation using piecewise cubic Hermite method
        
        output.temp(:,totaltemps-tempnum+1:totaltemps)=newtemp; %write newtemp to output
    end %for
    
    disp('Note: Sensors were sampled at different times:')
    disp('      Time series had to be trimmed and/or interpolated.')

end %if

% Concatenate all depth vectors in output.depth vector
output.depth=[]; %create blank output.depth variable
for argcount=3:3:nargin %go through all the depth vectors
    output.depth=horzcat(output.depth,varargin{argcount}); %append depth to output.depth vector
end %for

% Warn if depths are not monotonically increasing
if any(diff(output.depth)==0) %if any depth is the same as the previous depth
    warning('There are two temperature series with the same reported depth; this may cause undesired results.')
elseif any(diff(output.depth)<0) %if any depth is less than the previous depth
    warning('Depths are not monotonically increasing throughout the input arguments; this may cause undesired results.')
end %if

disp(' . . . Done!')

end %function
% 
% Copyright (c) 2011, Ryan P. Gordon.
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are
% met:
% (1) Redistributions of source code must retain the above copyright
% notice, this list of conditions and the following disclaimer.
% (2) Redistributions in binary form must reproduce the above copyright
% notice, this list of conditions and the following disclaimer in the
% documentation and/or other materials provided with the distribution.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
% IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
% THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
% PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
% CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
% EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
% PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
% PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
% LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
% NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
% SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.