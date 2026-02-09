function [output]=vflux_resample(input,rfactor)
%
% vlux_resample - Resampling component of VFLUX program, called by vflux.m
%
% Description:
% Filters and resamples temperature time series records with 'resample'
% function from Signal Processing Toolbox.  Requires the Signal Processing
% Toolbox.
%
% Usage:
%   output = vflux_resample(input, rfactor)
%
% Input:
%   input = a MATLAB structure containing input time series formatted by
%       vfluxformat.m (containing input.time, input.temp, and input.depth
%       arrays).
%   rfactor = a positive integer factor by which to reduce sampling rate.
%       For example, if original sampling rate is 72 samples/day, and the
%       desired reduced sampling rate is 12 samples/day, then
%       rfactor=72/12=6. A reduced sampling rate of approximately 12
%       samples/day is recommended. If rfactor=1, then no resampling is
%       performed.
%
% Output:
%   output.dtime = downsampled time vector
%   output.rtemp = resampled temp vector
%

% Written by Ryan Gordon, Syracuse University, January 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 106, updated 3/19/2011

% Check inputs
if nargin~=2
    error('Wrong number of input arguments; all input arguments are required.')
elseif isfield(input,'time')+isfield(input,'temp')+isfield(input,'depth')~=3
    error('The input structure must contain time, temp, and depth arrays, as created by VFLUXformat. Please run VFLUXformat.')
elseif isscalar(rfactor)==0 || rfactor<0 || mod(rfactor,1)~=0 %if rfactor is not a scalar positive integer
    error('rfactor must be a positive integer.')
end %if

% Special circumstances
if rfactor==1 %if rfactor=1, then outputs = (renamed) inputs
    output=input;
    output.dtime=input.time;
    output.rtemp=input.temp;
    disp('Note: rfactor was input as 1: resampling was not performed.')
    return
end %if

% Copy current contents of input to output
output=input;

% Downsample time
output.dtime=input.time(1:rfactor:end); %keeps every rfactor-th sample

% Reflect and mirror temp vectors around ends as padding to reduce edge effects of resample
temprows=size(input.temp,1); %number of rows in temp matrix
tempcols=size(input.temp,2);%number of columns in temp matrix
temppad(1:temprows*3,1:tempcols)=NaN; %preallocate temppad, 3 times length of temp
for col=1:tempcols %for each column in temppad, reflect and mirror:
    temppad(:,col)=[2*input.temp(1,col)-input.temp(end-1,col); 2*input.temp(1,col)-input.temp(end:-1:2,col); input.temp(:,col); 2*input.temp(end,col)-input.temp(end-1:-1:1,col); 2*input.temp(end,col)-input.temp(2,col)];
    %                                first element                first third (except first element)       middle=original data             last third (except last element)                 last element
end %for
if mod(temprows,rfactor)~=0 %if rfactor does not go evenly into number of rows in temp matrix
    temppad(1:mod(temprows,rfactor),:)=[]; %delete number of rows from the beginning equal to the remainder
end %if

% Resample temppad
rtemppad=resample(temppad,1,rfactor); %resample function with FIR (Kaiser window) low-pass filter

% Write output.rtemp as rtemppad without the padding
output.rtemp=rtemppad(floor(temprows/rfactor)+1:2*floor(temprows/rfactor)+1,:);
output.rtemp=output.rtemp(1:length(output.dtime),:); %trim rtemp to length of dtime, just in case (should very rarely be necessary)

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