function [output]=vflux_dhr(input,Pf)
%
% vlux_dhr - DHR component of VFLUX program, called by vflux.m
%
% Description:
% Runs ARSPEC, DHROPT, and DHR programs from the Captain Toolbox (Young et
% al. 2004), in order to filter out and keep the fundamental (typically
% diurnal) component of the harmonic signal, along with its amplitude and
% phase information. Requires the Captain Toolbox.
%
% Young, P.C., Taylor, C.J., Tych, W., Pegregal, D.J., McKenna, P.G., 2010.
% The Captain Toolbox. Centre for Research on Environmental Systems and
% Statistics, Lancaster University. (http://www.es.lancs.ac.uk/cres/captain).
%
% Usage:
%   output = vflux_dhr(input,Pf)
%
% Input:
%   input = a MATLAB structure containing input time series as formatted by
%       vfluxformat.m and vflux_resample.m, containing at least input.dtime
%       and input.rtemp arrays.
%   Pf = period of the fundamental frequency to filter, in days (typical
%       value is 1, for the diurnal signal)
%
% Output:
%   output.ftemp = filtered fundamental (diurnal) component of temp signal
%       (units of degrees C), in a matrix with the same length and number
%       of columns as input.rtemp.
%   output.amp = amplitude of fundamental component, in degrees C, in a
%       matrix of the same size as output.ftemp.
%   output.phs = phase of fundamental component, in radians, in a matrix of
%       the same size as output.ftemp.
%
% Aditional Switches exist (edit these in the m-code)

% Written by Ryan Gordon, Syracuse University, January 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 113, updated 11/02/2011

%%%%%%%%%%%%%%%%%% Aditional Switches %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Show/hide diagnostic plots. 1=pause after each output plot (slower, but
% best for determining quality of model fit to data), or 0=continue without
% pausing (faster, but the plots won't be visible).
    show_plots=1;

% ARorder is a positive integer specifying the Auto-Regression spectrum
% order in ARSPEC program.  A positive integer=set AR order for all temp
% columns, 0=AR order is automatically chosen by AIC algorithm for each
% temp column, -1=set ARorder equal to the period of the fundamental
% (diurnal) component (in samples per cycle), rounded to the nearest
% integer. See the Captain Toolbox ARSPEC documentation for more.
    ARorder=-1;

% Uncomment only ONE of the following statements for pstring (or edit them
% or create your own). The command pstring will be evaluated later in the
% program to define the vector P; P is an input to the DHR program that
% indicates the periods (in samples per cycle) of the trend and harmonic
% components that will be identified and filtered by DHR. '0' represents
% the trend. 'Pfs' refers to the fundamental (diurnal) period.  Therefore
% 'Pfs/2 is the period of the first harmonic, and 'Pfs/3' is the period of
% the second harmonic, etc. 'components'  specifies the periods of the
% fundamental (diurnal) component, and all its harmonics down to the
% Nyquist frequency. A positive integer represents the
% period (in samples per cycle) of a specific component. The fundamental
% component must be included. In general, it is usually wise to also
% include the trend and at least the first harmonic. See the Captain
% Toolbox ARSPEC, DHR, and DHROPT documentation for more.
    %pstring = 'P=[0 Pfs Pfs/2 Pfs/3]' ;         %filters trend, fundamental, and first and second harmonics
    %pstring = 'P=[0 components]' ;              %filters trend, fundamental, and all harmonics down to the Nyquist frequency
% In the following pstring examples, peaks from ARSPEC are used to define
% some of the component periods, so that these components can vary with the
% spectrum of each specific timeseries as determined by ARSPEC, while other
% components (usually the trend and fundamental) will be held constant.
% Use 'pks(x)' to indicate the period of the x-th peak identified by the
% ARSPEC program. This only works well if the AR spectrums are clean and
% consistent, without spurious peaks.
    pstring = 'P=[0 Pfs pks(3) pks(4)]' ;        %filters trend, fundamental, and third and fourth peaks from ARSPEC (often the first and second harmonics)
    %pstring = 'P=[0 pks(2) pks(3) pks(4)]' ;    %filters trend, and second through fourth peaks from ARSPEC (often the fundamental and first two harmonis)

% TVP is a switch in the DHROPT program that determines the NVR model to
% use in optimization for trend (first element of TVP) and harmonic
% components (second element of TVP). See the Captain Toolbox DHR and
% DHROPT documentation. 0=Random Walk, and 1=Integrated Random Walk.
% Typically, either [1 0] or [0 0] seem to work best.
    TVP=[0 0];
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if evalin('caller','unattend'), show_plots=0; end %disables diagnostic plots if unattend switch set in vflux.m

% Error check inputs
if nargin~=2
    error('Wrong number of input arguments; all input arguments are required.')
elseif isfield(input,'dtime')+isfield(input,'rtemp')~=2
    error('The input structure must contain dtime and rtemp arrays, as created by vflux_resample. Please run vflux_resample.')
elseif isscalar(Pf)~=1
    error('Pf must be a scalar.')
elseif show_plots~=0 && show_plots~=1
    error('show_plots must equal 0 or 1')
elseif isscalar(ARorder)~=1 || ARorder<-1 || mod(ARorder,1)~=0 %if ARorder is not a scalar integer >=-1
    error('ARorder must be an integer >= -1.')
elseif ischar(pstring)~=1
    error('pstring must be a character string (text enclosed in single quotes) that defines the P variable.')
elseif any(TVP~=0 & TVP~=1) %if any element of TVP is not 0 or 1
    error('TVP must be a vector of ones and/or zeros.')
end %if

% Copy current contents of input to output
output=input;

% Calculate periods (in samples per cycle) of fundamental and harmonic components of dirunal signal, and save in 'components' vector
Rs=round((length(input.dtime)-1)/(input.dtime(end)-input.dtime(1))*1000)/1000; %sampling rate of downsampled time 'input.dtime' (in samples per day, rounded to three decimals)
Pfs=Rs*Pf; %the period (in samples per cycle) of the fundamental (diurnal) signal
if ARorder==-1, ARorder=round(Pfs); end %if ARorder switch, above, is -1, substitute fundamental period for ARorder
disp(sprintf('Note: ARorder set to %d.',ARorder))
components=Pfs;
compcount=2;
while components(end)>=2 %loop while period (in samples per cycle) is >= the Nyquist period (in samples/cycle)
        %NOTE: By definition, Nyquist period will always be 2 samples long, independent of sampling frequency, etc.
        %      (Nyquist freq in cycles/day is 1/2 the sampling freq in samples/day.)
    components(compcount)=Pfs/compcount; %populate components vector with component periods
    compcount=compcount+1;
end %while

% Preallocate outputs
if isfield(output,'ftemp'), output=rmfield(output,'ftemp'); end %clears ftemp field if it already existed from a previous run
if isfield(output,'amp'), output=rmfield(output,'amp'); end
if isfield(output,'phs'), output=rmfield(output,'phs'); end
output.ftemp(1:size(input.rtemp,1),1:size(input.rtemp,2))=NaN;
output.amp=output.ftemp;
output.phs=output.ftemp;

for col=1:size(input.rtemp,2) %for each column in input.rtemp:
    
    disp(sprintf('Processing sensor at %f meters depth . . .',input.depth(col)))
    
    % Run ARSPEC to create plots and 'pks' vector
    [amp,t,pks,amps]=arspec(input.rtemp(:,col),ARorder,[1 0],1032,components); %run ARSPEC with ARorder and vertical lines at component periods
    if show_plots==1, disp('Pause for plot: press any key to continue.'), pause, end %pause for plot

    % Make P vector from pstring
    pks=[pks,nan(1,24)]; %append a bunch of NaN values to end of pks vector as padding. This is in case pstring references ARSPEC peaks that do not exist.
    components=[components,nan(1,24)]; %append NaN's to end of components vector, for same reason.
    eval([pstring ';']); %evaluate pstring as a command, which creates the vector P
    P(isnan(P))=[]; %delete all NaN values in P
    components(isnan(components))=[]; %delete all NaN values in components
        
    % Run DHROPT to find optimized nvr parameters for DHR program
    nvr=dhropt(input.rtemp(:,col),P,TVP,ARorder); %run DHROPT with P, TVP, and ARorder, all defined above
    if show_plots==1, disp('Pause for plot: press any key to continue.'), pause, end %pause for plot
    
    % Run DHR using nvr values from DHROPT
    [fit,fitse,tr,trse,comp,e,amp,phs]=dhr(input.rtemp(:,col),P,TVP,nvr);
    
    % Plot the original data, fit, trend, harmonic components, and residual
    if show_plots==1
        plot(input.dtime,[input.rtemp(:,col), fit, tr(:,1), fit-input.rtemp(:,col), amp(:,1), comp,]) %plot
        xlabel('time (days)'), set(gca,'XTickLabel',num2str(get(gca,'XTick')')), ylabel('temperature (degrees C)'), title('DHR Results') %format axes labels and title
        warning off all, legend('time series','fit to time series','trend','residual','fundamental amplitude','fundamental component','first harmonic component','second harmonic component','third harmonic component','fourth harminc component','Location','East'), warning on all %create legend (and suppress warnings about legend entries)
        disp('Pause for plot: press any key to continue.'), pause %pause for plot
    end %if
    close %close any open figure window
    
    % Fix the phase angle jump problem in the 'phs' output from DHR
    fphs=phs; %new variable 'fphs' for the fixed phase
    while 1==1
        jump=0; %(re)set jump counter
        for k=2:length(fphs) %for each element 'k' of phs from 2 to end
            if fphs(k)-fphs(k-1)<-2 %if difference between current element and previous element is less than -2 (a jump from +pi/2 to -pi/2)
                fphs(k)=fphs(k)+pi; %add pi to current element value
                jump=jump+1;
            elseif fphs(k)-fphs(k-1)>2 %if difference between current element and previous element is greater than +2 (a jump from -pi/2 to +pi/2)
                fphs(k)=fphs(k)-pi; %subtract pi from current element value
                jump=jump+1;
            end %if
        end %for k
        if jump==0, break, end %break out of while loop if all jumps are fixed
    end %while
    
    % Save signal, amplitude, and fixed phase of the fundamental component to output
    output.ftemp(:,col)=comp(:,1);
    output.amp(:,col)=amp(:,1);
    output.phs(:,col)=fphs(:,1);

end %for col

% Create and fill in some cells of parameters output file, but only if called by vflux
if evalin('caller','exist(''vfluxversion'')') %if called by vflux (i.e. if vfluxversion exists in the caller workspace)
    output.parameters=cell(4,14); %create output.parameters as empty cell array
    output.parameters(4,10)={ARorder}; %write ARorder (as used) to output.parameters
    output.parameters(4,11)={pstring}; %write contents of pstring
    output.parameters(4,12)={TVP}; %write TVP
end %if

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