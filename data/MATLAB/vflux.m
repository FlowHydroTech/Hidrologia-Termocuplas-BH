function [output]=vflux(sinput,rfactor,windows,Pf,n,beta,Kcal,Cscal,Cwcal,unattend)
%
% VFLUX - Vertical Fluid Heat Transfer Solver  [ VFlu[H]X Solver ]  
% 
% Description:
%   VFLUX is a program that calculates one-dimensional vertical fluid flow
%   (seepage flux) through saturated porous media, using heat transport
%   equations developed by Hatch et al. (2006) and Keery et al. (2007). It
%   uses temperature time series data measured by multiple temperature
%   sensors in a vertical profile in order to calculate flux at specific
%   times and depths.
%
%   Data is input into VFLUX as a MATLAB structure formatted by the
%   VFLUXFormat program, which contains columns of time and temperature
%   data, as well as the depths of each sensor in the vertical profile.
%   VFLUX processes the time series by optionally resampling the data to a
%   lower sampling rate, in order to reduce the filtering problems
%   associated with oversampling.  The program then filters each time
%   series using Dynamic Harmonic Regression (DHR) programs from the
%   Captain Toolbox (Young et al. 2004), isolating a fundamental
%   temperature signal identified by its period of oscillation (typically a
%   diurnal signal).  Finally, the program calculates vertical flux between
%   pairs of temperature sensors using the amplitudes and phases of their
%   filtered temperature signals, according to Hatch et al. (2006) and
%   Keery et al. (2007).
%
%   Required toolboxes: MATLAB Signal Processing Toolbox (or another
%   resample function), and the Captain Toolbox.
%
%   Hatch, C.E.,Fisher, A.T., Revenaugh, J.S., Constantz, J., Ruehl, C.,
%   2006. Quantifying surface water-groundwater interactions using time
%   series analysis of streambed thermal records: Method development. Water
%   Resources Research, 42(10), W10410.
%   Keery, J., Binley, A., Crook, N., Smith, J.W.N., 2007. Temporal and
%   spatial variability of groundwater-surface water fluxes: Development
%   and application of an analytical method using temperature time series.
%   Journal of Hydrology, 336(1-2), 1-16.
%   Young, P.C., Taylor, C.J., Tych, W., Pegregal, D.J., McKenna, P.G.,
%   2010. The Captain Toolbox. Centre for Research on Environmental Systems
%   and Statistics, Lancaster University.
%   (http://www.es.lancs.ac.uk/cres/captain).
%   McCallum, A., Andersen, M.S., Rau, G.C., Acworth, R.I., 2012. A 1-D %+
%   method for estimating surface water--groundwater interactions and   %+
%   effective thermal diffusivity using temperature time series. Water  %+
%   Resources Research, 48, W11532                                      %+
%   Luce, C.H., Tonina, D., Gariglio, F., Applebee, R., 2013. Solutions %+
%   for the diurnally forced advection-diffusion equation to estimate   %+
%   bulk fluid velocity and diffusivity in streambeds from temperature  %+
%   time series, Water Resources Research, 49, doi:10.1029/2012WR012380 %+
%
% Usage:
%   output = vflux(input, rfactor, windows, Pf, n, beta, Kcal, Cscal, Cwcal, unattend)
%
% Input:
%   input = a MATLAB structure containing input time series formatted by
%       VFLUXFormat, containing arrays input.time, input.temp, and
%       input.depth. (See vfluxformat.m or type 'help vfluxformat'.)
%   rfactor = a positive integer factor by which to reduce sampling rate.
%       For example, if original sampling rate is 72 samples/day, and the
%       desired reduced sampling rate is 12 samples/day, then
%       rfactor=72/12=6. A reduced sampling rate of approximately 12
%       samples per fundamental cycle (see Pf, below) is recommended. If
%       rfactor=1, then no resampling is performed. If rfactor=0, then
%       VFLUX will calculate an appropriate integer rfactor so that the
%       reduced sampling rate is close to 12 samples per fundamental cycle
%       (as input as Pf).
%   windows = a scalar or vector of positive integers, where each element
%       is a sliding sensor spacing "window", in sensor-spacings, used to
%       identify sensor pairs for flux calculations. VFLUX will calculate
%       flux between all the sensor pairs that are separated by the
%       "window"-number of sensor-spacings. For example, if there are 5
%       sensors in the profile and windows=1, VFLUX will calculate fluxes
%       between sensors 1 and 2, 2 and 3, 3 and 4, and 4 and 5 (the
%       "window" is one sensor-spacing).  If windows=[1 2], then VFLUX will
%       calculate fluxes between the above pairs, plus between sensors 1
%       and 3, 2 and 4, and 3 and 5 (the "window" here is two spacings).
%       By including 3 in the windows vector, sensor pairs 1 and 4 and 2
%       and 5 would also be included. If windows=4, then flux would only be
%       calculated between sensors 1 and 5.
%   Pf = period of the fundamental temperature signal to filter and use for
%       flux calculations, in days. (The typical value is 1 day, for the
%       diurnal signal.)
%   n = total porosity (a typical value is 0.28).
%   beta = dispersivity, in meters (a typical value is 0.001).
%   Kcal = thermal conductivity, in cal/s-cm-C (a typical value is 0.0045).
%   Cscal = volumetric heat capacity of the sediment, in cal/cm^3-C
%       (typical value is 0.5).
%   Cwcal = volumetric heat capacity of the water, in cal/cm^3-C (typical
%       value is 1.0).
%   unattend = an optional switch to control user interaction with VFLUX.
%       Enter the text string 'unattended' for this input variable to
%       supress all pauses and user-input questions during normal
%       opporation, including the diagnostic DHR plots, flux calculation
%       errors, and post-run visualization, sensor-spacing optimization,
%       and sensitivity routines.
%
% Output:
%  ouput = a MATLAB structure containing the following arrays:
%   All arrays that were in the input structure.
%   output.dtime = the downsampled time vector, which contains every
%       rfactor-th sample from input.time, starting from the first sample.
%   output.rtemp = the resampled temp matrix with the same number of rows
%       as output.dtime. Created using the MATLAB resample function (part
%       of the Signal Processing Toolbox), using the default FIR low-pass
%       filter (Kaiser window).
%   output.ftemp = the filtered fundamental (diurnal) component of the temp
%       signal at each time in output.dtime, in units of degrees C, in a
%       matrix with the same length and number of columns as output.rtemp.
%   output.amp = amplitude of the fundamental component at each time in
%       output.dtime, in degrees C, in a matrix of the same size as
%       output.rtemp.
%   output.phs = phase of fundamental component at each time in
%       output.dtime, in radians, in a matrix of the same size as
%       output.rtemp.
%   output.fluxinfo = a metadata matrix that contains information about the
%       columns in the other flux result matrices (fluxha, etc.). Each
%       column represents a sensor pair for which fluxes were calculated.
%       For each column, the first row contains the window used, the second
%       row contains the depth of the upper sensor, the third row contains
%       the depth of the lower sensor, and the fourth row contains the
%       center-of-pair depth (the average of the upper and lower depths).
%   output.fluxha = vertical flux in meters/second, calculated with the
%       Hatch Amplitude method, at each time in output.dtime. Positive
%       values are downward flux, and negative are upward. Each column
%       contains results from the sensor pair indicated in output.fluxinfo.
%       Matrix has the same number of rows as output.dtime, and same number
%       of columns as output.fluxinfo.
%   output.fluxhp = vertical flux in meters/second, calculated with the
%       Hatch Phase method, at each time in output.dtime and for each
%       sensor pair in output.fluxinfo.
%   output.fluxka = vertical flux in meters/second, calculated with the
%       Keery Amplitude method, at each time in output.dtime and for each
%       sensor pair in output.fluxinfo.
%   output.fluxkp = vertical flux in meters/second, calculated with the
%       Keery Phase method, at each time in output.dtime and for each
%       sensor pair in output.fluxinfo.
%   output.fluxm  = vertical flux in meters/second, calculated with the    %+
%       McCallum method, at each time in output.dtime and for each sensor  %+
%       pair in output.fluxinfo                                            %+
%   output.Kem  = Effective thermal diffusivity in meters^2/second for     %+
%       McCallum method, at each time in output.dtime and for each sensor  %+
%       pair in output.fluxinfo                                            %+
%   output.fluxl  = vertical flux in meters/second, calculated with the    %+
%       Luce method, at each time in output.dtime and for each sensor pair %+
%       in output.fluxinfo                                                 %+
%   output.Kel  = Effective thermal diffusivity in meters^2/second for     %+
%       every output.dtime and for each sensor pair in output.fluxinfo     %+
%   output.scour = Scour (m) calculated from Luce et al. (2013)            %+
%   output.parameters = a cell array that records the input parameters and
%       other program settings that were used to run vflux.  The first row
%       of parameters is the name of the parameter, the second row is the
%       input variable that represents the parameter, the third row is the
%       units of the parameter, and the fourth row is the value of the
%       parameter.  Some cells (such as in the units row) are left empty by
%       design.
% 
% Example:
%   profile01 = vflux(profile01, 0, [1 2], 1, 0.28, 0.001, 0.0045, 0.5, 1)
%  [  output  = vflux(input, rfactor, windows, Pf, n, beta, Kcal, Cscal, Cwcal) ]
%
%       or, to supress all user interaction:
%
%   profile01 = vflux(profile01, 0, [1 2], 1, 0.28, 0.001, 0.0045, 0.5, 1, 'unattended')
%  [  output  = vflux(input, rfactor, windows, Pf, n, beta, Kcal, Cscal, Cwcal, unattend) ]
%
% Note: Aditional Switches exist for enabling the Hatch Amplitude
% derivative check and other options (edit these in the m-code).

% Written by Ryan Gordon, Syracuse University, January 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 119, updated 03/13/2015 

vfluxversion='VFLUX 2.0.0';                                             %+

% Hatch Amplitude derivative check option.  See Hatch et al. 2006, section 3.1 for details.
% If enabled, vflux_flux.m will write NaN for any flux value for which the derivative dAr/dq (amplitude ratio with respect to seepage flux) is below the limit.
if 0  %write this line as "if 1" to enable, or "if 0" to disable (default is 0)
    dArdq_limit = 0.001; %enter desired limit (in units of days/meter). Hatch et al. 2006 uses a value of 0.001 d/m.
end %if

% Undocumented option to output the amplitude ratio as a separate matrix 'output.ampratio' and the phase lag (in radians) as 'output.phaselag' for testing purposes
outputAr = 1; %set as 1 to enable, 0 to disable (default is 0)

% Check input arguments
if nargin<9
    error('Wrong number of input arguments.')
elseif isfield(sinput,'time')+isfield(sinput,'temp')+isfield(sinput,'depth')~=3
    error('The input structure must contain time, temp, and depth arrays, as created by VFLUXFormat. Please run VFLUXFormat.')
elseif isscalar(rfactor)==0 || rfactor<0 || mod(rfactor,1)~=0 %if rfactor is not a scalar positive integer
    error('rfactor must be a positive integer.')
elseif isvector(windows)==0 || any(windows<1) || any(mod(windows,1)~=0) %if windows is not a vector/scalar positive integer
    error('windows must be a scalar or vector of positive integers.')
elseif isscalar(Pf)+isscalar(n)+isscalar(beta)+isscalar(Kcal)+isscalar(Cscal)+isscalar(Cwcal)~=6
    error('n, beta, Kcal, Cscal, Cwcal and Pf must all be scalars.')
end %if

if nargin==9, unattend='no'; end %create 'unattend' input argument if not entered in function call
unattend=strcmpi(unattend,'unattended'); %set unattend to logical 1 if input as 'unattended', logical 0 otherwise

disp(' ')
disp(vfluxversion)
disp(' ')
disp('Beginning resample . . .')

% Lowpass filter and resample (to avoid oversampling) by calling vflux_resample: creates sinput.dtime and sinput.rtemp
Rs=(length(sinput.time)-1)/(sinput.time(end)-sinput.time(1)); %sampling rate of 'sinput.time' (in samples per day)
if rfactor==0 %if rfactor=0, then calculate appropriate rfactor so that reduced sampling rate is between 12 and 24 samples/cycle
    rfactor=floor((Rs+0.0001)*Pf/12);  %(add a small number to Rs to avoid binary floating point errors)
    disp(sprintf('Note: rfactor was input as 0: the resampling factor was calculated to be %0.0f.',rfactor))
    disp(sprintf('The reduced sampling rate is therefore %0.3f samples/day, or %0.3f samples per fundamental cycle.',Rs/rfactor,Rs*Pf/rfactor))
else
    disp(sprintf('Note: rfactor was input as %0.0f.  The reduced sampling rate is therefore %0.3f samples/day,',rfactor,Rs/rfactor))
    disp(sprintf('or %0.3f samples per fundamental cycle.',Rs*Pf/rfactor))
end %if
output_resample=vflux_resample(sinput,rfactor); %call to vflux_resample

disp(' . . . Done!')
disp(' ')
disp('Beginning DHR filtering . . .')

% DHR filter to extract diurnal signal by calling vflux_dhr: creates sinput.ftemp, sinput.amp, and sinput.phs
output_dhr=vflux_dhr(output_resample,Pf); %call to vflux_dhr

disp(' . . . Done!')
disp(' ')
disp('Beginning flux calculations . . .')

% Preallocate flux results matrices
clearvars fluxha fluxhp fluxka fluxkp
pairs=sum(length(sinput.depth)-windows); %total number of sensor pairs that will be analyzed
fluxha(1:size(output_dhr.ftemp,1),1:pairs)=NaN; %flux from Hatch amplitude method
fluxhp=fluxha; %flux Hatch phase
fluxka=fluxha; %flux Keery amplitude
fluxkp=fluxha; %flux Keery phase
fluxm =fluxha; %flux McCallum Equation 11                                %+
Kem =fluxha;   %thermal diffusivity from McCallum Equation 12            %+
fluxl =fluxha; %flux from Luce Equation 64d                              %+
Kel =fluxha; %thermal diffusivity from Luce Equation 64c                 %+
dzl =fluxha; %scour from Luce Equation 57                              %+
fluxinfo(1:4,1:pairs)=NaN; %metadata info matrix for flux results

% Run flux calculation routine for all pairs:
if unattend %if unattend flag set as logical 1
    nopause=1; %then also set nopause flag to 1 (for use in vflux_flux.m)
else
    nopause=[]; %otherwise set pause indicator to empty (for use in vflux_flux.m)
end %if
Ps=(output_dhr.dtime(end)-output_dhr.dtime(1))/(length(output_dhr.dtime)-1); %sampling period of sinput.dtime, in days
for wincol=1:length(windows) %for each sensor window (column in windows)
    window=windows(wincol); %get sensor window
    for sens=1:length(sinput.depth)-window %for each sensor (column in depth), except last sensor(s) for which mate(s) d.n.e.
        z=sinput.depth(sens+window)-sinput.depth(sens); %calculate sensor spacing
        
        % Create names array for variables, which will be passed to
        % vflux_flux.m, in order to populate error and warning messages  %+ I haven't added anything here for the McCallum or Luce Methods
        upperampname=[inputname(1) '.amp column ' num2str(sens)];
        lowerampname=[inputname(1) '.amp column ' num2str(sens+window)];
        upperphsname=[inputname(1) '.phs column ' num2str(sens)];
        lowerphsname=[inputname(1) '.phs column ' num2str(sens+window)];
        names={upperampname lowerampname upperphsname lowerphsname};
        
        % Calculate fluxes by calling vflux_flux
        fluxes=vflux_flux(output_dhr.amp(:,sens),output_dhr.amp(:,sens+window),output_dhr.phs(:,sens),output_dhr.phs(:,sens+window),z,n,beta,Kcal,Cscal,Cwcal,Pf*24,Ps*24,names,nopause);
        
        % Write flux results to matrices
        if wincol>1
            pair=sum(length(sinput.depth)-windows(1:wincol-1))+sens; %this is the ordinal number of the current pair (for writing results to correct column)
        else pair=sens;
        end %if
        fluxha(:,pair)=fluxes(:,1); %write Hatch amp results
        fluxhp(:,pair)=fluxes(:,2); %write Hatch phs results
        fluxka(:,pair)=fluxes(:,3); %write Keery amp results
        fluxkp(:,pair)=fluxes(:,4); %write Keery phs results
        fluxm(:,pair) =fluxes(:,7); %write McCallum flux results                %+
        Kem(:,pair)   =fluxes(:,8); %write McCallum thermal diffusivity results %+  
        fluxl(:,pair) =fluxes(:,9); %write Luce flux results                    %+  
        Kel(:,pair)   =fluxes(:,10);%write Luce thermal diffusivity results     %+  
        dzl(:,pair)   =fluxes(:,11);%write Luce scour results     %+ 
        
        fluxinfo(1,pair)=window; %write window to row 1 of fluxinfo
        fluxinfo(2,pair)=sinput.depth(sens); %write upper pair depth to row 2 of fluxinfo
        fluxinfo(3,pair)=sinput.depth(sens+window); %write lower pair depth to row 3 of fluxinfo
        fluxinfo(4,pair)=(sinput.depth(sens+window)+sinput.depth(sens))/2; %write center-of-pair depth to row 4 of fluxinfo
        
        % Undocumented section to output amplitude ratio and phase lag (in radians) in separate output matrices
        if outputAr==1
            if wincol==1 && sens==1, ampratio=[]; phaselag=[]; end %clear ampratio and phaselag if they existed from previous run
            ampratio(:,pair)=fluxes(:,5); %write amp ratio to ampratio matrix
            phaselag(:,pair)=fluxes(:,6); %write phase lag (in radians) to phaselag matrix
        end %if
        
    end %for sens
end %for wincol

% Write results to output
output=output_dhr; % Copy current contents of output_dhr to output
if outputAr==1, output.ampratio=ampratio; output.phaselag=phaselag; end
output.fluxha=fluxha;
output.fluxhp=fluxhp;
output.fluxka=fluxka;
output.fluxkp=fluxkp;
output.fluxm=fluxm;               %+
output.Kem=Kem;                   %+ 
output.fluxl=fluxl;               %+
output.Kel=Kel;                   %+
output.dzl=dzl;                   %+
output.fluxinfo=fluxinfo;

% Fill in remainder of output.parameters cell array (created by vflux_dhr.m)
output.parameters(1,1:14)={'fundamental period' 'total porosity' 'thermal dispersivity' 'baseline thermal conductivity' 'volumetric heat capacity of sediments' 'volumetric heat capacity of water' 'volumetric heat capacity of system' 'thermal diffusivity' 'reduced sampling rate' 'ARorder used' 'P command' 'TVP' 'program version' 'time stamp'};
output.parameters(2,1:12)={'Pf' 'n' 'beta' 'Kcal' 'Cscal' 'Cwcal' '(calculated)' '(calculated)' '(calculated)' '(calculated)' 'pstring' 'TVP'};
output.parameters(3,1:9)={'days' '(unitless)' 'm' 'cal/s-cm-C' 'cal/cm3-C' 'cal/cm3-C' 'cal/cm3-C' 'cm2/s' 'samples/day'};
output.parameters(4,1:9)={Pf n beta Kcal Cscal Cwcal (n*Cwcal+(1-n)*Cscal) Kcal/(n*Cwcal+(1-n)*Cscal) Rs/rfactor};
output.parameters(4,13)={vfluxversion};
timestamp=clock; %get current system time as a vector
output.parameters(4,14)={[num2str(fix(timestamp(2))) '/' num2str(fix(timestamp(3))) '/' num2str(fix(timestamp(1))) ' ' num2str(fix(timestamp(4))) ':' num2str(fix(timestamp(5))) ':' num2str(fix(timestamp(6)))]};

disp(' . . . Done!')

% Run vflux_post for visualization, sensor spacing, and sensitivity routines
if ~unattend
    disp(' ')
    disp('VFLUX is finished calculating flux results.')
    disp('Would you like to plot results?') 
    runpost=input('Enter 1 to start post-calculation routine, or press ENTER to exit the program: ');
else runpost=0;
end %if
if runpost==1
    vflux_post(output) %call to vflux_post.m
end %if

disp(' ')
disp('VFLUX finished successfully.')

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