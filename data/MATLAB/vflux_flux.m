function [fluxes]=vflux_flux(upper_amp,lower_amp,upper_phs,lower_phs,z,n,beta,Kcal,Cscal,Cwcal,P,Ps,inputname,nopause)
%
% vlux_flux - Flux component of VFLUX program, called by vflux.m  
% 
% Description:
% This function calculates seepage flux (q) using the Hatch et al. 2006
% methods based on amplitude and phase, and the Keery et al. 2007 methods
% based on amplitude and phase, using output from a Dynamic Harmonic
% Regression (DHR) analysis.
% 
% Hatch, C.E.,Fisher, A.T., Revenaugh, J.S., Constantz, J., Ruehl, C.,
% 2006. Quantifying surface water-groundwater interactions using time
% series analysis of streambed thermal records: Method development. Water
% Resources Research, 42(10), W10410.
% 
% Keery, J., Binley, A., Crook, N., Smith, J.W.N., 2007. Temporal and
% spatial variability of groundwater-surface water fluxes: Development and
% application of an analytical method using temperature time series.
% Journal of Hydrology, 336(1-2), 1-16.
%
% McCallum, A., Andersen, M.S., Rau, G.C., Acworth, R.I., 2012. A 1-D   %+
% method for estimating surface water--groundwater interactions and     %+
% effective thermal diffusivity using temperature time series. Water    %+
% Resources Research, 48, W11532                                        %+        
%                                                                       %+
% Luce, C.H., Tonina, D., Gariglio, F., Applebee, R., 2013. Solutions   %+
% for the diurnally forced advection-diffusion equation to estimate     %+
% bulk fluid velocity and diffusivity in streambeds from temperature    %+
% time series, Water Resources Research, 49, doi:10.1029/2012WR012380   %+ 
%
% Usage:
%     fluxes = vflux_flux(upper_amp, lower_amp, upper_phs, lower_phs, z, n, beta, Kcal, Cscal, Cwcal, P, Ps, inputname, nopause)
%
% Input:
%     upper_amp = column vector of amplitudes from upper sensor, in degrees C
%     lower_amp = column vector of amplitudes from lower sensor, in degrees C
%     upper_phs = column vector of phases from upper sensor, in radians (see note below)
%     lower_phs = column vector of phases from lower sensor, in radians (see note below)
%     z = vertical spacing of temperature sensors, in meters
%     n = total porosity n (unitless)
%     beta = dispersivity, in meters
%     Kcal = baseline thermal conductivity, lambda, in cal/s-cm-C
%     Cscal = volumetric heat capacity of sediments, Cs, in cal/cm^3-C
%     Cwcal = volumetric heat capacity of water, Cw, in cal/cm^3-C
%     P = periodicity of temperature signal, in hours (typically 24)
%     Ps = periodicity of sampling (sample period), in hours (for example, 2)
%     inputname = an optional cell array containing four character arrays,
%         which are identifying names for the first four input arguments.
%         Used by calling function vflux.m.
%     nopause = an optional pause indicator, for use by calling function
%         vflux.m. If set as empty, i.e. [], will allow pauses.  If set as
%         1, will suppress pauses.
%
% Output:    
%   fluxes = an eleven-column matrix of the same length as the input vectors. 
%     Column 1  is flux (m^3/m^2-s) calculated from the Hatch amplitude ratio method.
%     Column 2  is flux (m^3/m^2-s) calculated from the Hatch phase difference method.
%     Column 3  is flux (m^3/m^2-s) calculated from the Keery amplitude ratio method.
%     Column 4  is flux (m^3/m^2-s) calculated from the Keery phase difference method.
%     Column 5  is Ar (°C)                                                            %+
%     Column 6  is phaselag (radians)                                                 %+
%     Column 7  is flux (m^3/m^2-s) calculated from the McCallum method.              %+
%     Column 8  is thernal diffusivitty (m^2/s) calculated from the McCallum method.  %+    
%     Column 9  is flux (m^3/m^2-s) calculated from the Luce method.                  %+    
%     Column 10 is thernal diffusivitty (m^2/s) calculated from the Luce method.      %+   
%     Column 11 is dz (m) calculated from the Luce method.      %+   
% NOTE: Flux (q) is not divided by effective porosity, and therefore is not a true velocity (v-bar).
%

% Written by Ryan Gordon, Syracuse University, November 2010
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244    
%   Contact: rpgordon@syr.edu
% Hatch Amplitude Method code written by Jeff McKenzie, February 2010
% McCallum and Luce method functionality added by Dylan Irvine, March 2015
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 121, updated 03/13/2015

% Check input arguments
if nargin<12 || nargin>14
    error('Wrong number of input arguments; 12 input arguments are required.')
elseif isvector(upper_amp)+isvector(lower_amp)+isvector(upper_phs)+isvector(lower_phs)~=4
    error('All amp and phs inputs must be vectors')
elseif isscalar(z)+isscalar(n)+isscalar(beta)+isscalar(Kcal)+isscalar(Cscal)+isscalar(Cwcal)+isscalar(P)+isscalar(Ps)~=8
    error('n, beta, Kcal, Cscal, Cwcal and Pf must all be scalars.')
elseif length(upper_amp) ~= length(lower_amp)
    error('Upper and lower amp data are different lengths: %s and %s',char(inputname(1)),char(inputname(2)))
elseif length(upper_phs) ~= length(lower_phs)
    error('Upper and lower phase data are different lengths: %s and %s', char(inputname(3)),char(inputname(4)))
elseif length(upper_amp) ~= length(upper_phs)
    error('Amp and phase data are different lengths: %s and %s',char(inputname(1)),char(inputname(3)))
else
    datalength = length(upper_amp);
end
if nargin<14, nopause=[]; end

% Preallocate results matrix...    %+
fluxes(1:datalength,1:11)=NaN;

% Unit Conversions
K = Kcal*4.18400*100*60*60; % baseline thermal conductivity, in J/hr-m-C
C = (n*Cwcal+(1-n)*Cscal)*4.18400*100^3;  % volumetric heat capacity of system, in J/m^3-C
Cw = Cwcal*4.18400*100^3;  % volumetric heat capacity of water, in J/m^3-C

% Calculate Hatch ratios
heat_capacity_ratio = C / Cw;  %Heat capacity ratio: gamma in Hatch
Ke = K/C;    % effective thermal diffusivity, without the beta term, in m^2/hr

%%%%%%%%%% CALCULATE FLUXES for each row in input vectors %%%%%%%%%%
for rowcount = 1:datalength;
    
    % Calculate phase difference (lag time)
    phaselag = lower_phs(rowcount) - upper_phs(rowcount);  %phase lag (in radians)
    if phaselag<-pi/2, phaselag=phaselag+pi; end %to correct for possible phase jump (pi/2 to -pi/2) in DHR output between upper and lower sensors, when time lag is really positive but appears highly negative.
        %A value of <-pi/2 in line above will correctly identify positive time lags (where a phase jump occurs) of up to 1/4 cycle.
        %Change to <-pi/4 to increase sensitivity up to 1/2 cycle, but watch out for truly negative time lags in bad data.
    timelag = P * phaselag / (2*pi);  %phase lag (in hours)
    samplelag = timelag / Ps;  %phase lag (in number of samples)
    roundlag = round(samplelag);  %phase lag in samples rounded to the nearest sample
    
    
    % If roundlag is less than 0 or is NaN, display warning and set to 0
    if roundlag<0 || isnan(roundlag)
        disp('Warning: Phase difference is negative:')
        disp(['       ' char(inputname(3)) ' and ' char(inputname(4)) ' at row ' num2str(rowcount) '.'])
        disp('       Using a phase difference of zero to calculate amplitude methods.')
        roundlag=0;
        if isempty(nopause)
            nopause=input('Press ENTER to continue, or type 1 then ENTER to suppress all further pauses: ');
        end %if nopause
    end %if
    
    % Write NaN's to results vector and end loop if the current row plus lag exceeds data length
    if rowcount+roundlag>datalength
        fluxes(rowcount,:)=NaN;
        continue
    end %if
    
    % Calculate amplitude ratio
    Ar=lower_amp(rowcount+roundlag) / upper_amp(rowcount);  %Ar is the Amplitude Ratio
    
    % Undocumented section to output amplitude ratios and phase lags in 5th and 6th columns of 'fluxes' matrix.  Enable or disable this line using 'outputAr' switch in vflux.m.
    if evalin('caller','exist(''outputAr'')') && evalin('caller','outputAr') %if outputAr set to 1 in vflux.m
        fluxes(rowcount,5)=Ar; %write amp ratio in 5th column
        fluxes(rowcount,6)=phaselag; %write phaselag (in radians) in 6th column
    end %if
    
    % Display error and write NaNs if Ar is larger than 1.
    if Ar>1.001
        disp('Warning: Lower amplitude is larger than upper amplitude:')
        disp(['       ' char(inputname(1)) ' and ' char(inputname(2)) ' at row ' num2str(rowcount) '.'])
        disp('       Cannot calculate amplitude methods: writing NaN.')
        fluxes(rowcount,1)=NaN;
        fluxes(rowcount,3)=NaN;
        if isempty(nopause)
            nopause=input('Press ENTER to continue, or type 1 then ENTER to suppress all further pauses: ');
        end %if nopause
    % Display error and write NaNs if Ar is close to 1
    elseif Ar>=0.99999  % Decrease this number to cut off artificially high flux rates due to sensor rounding errors, or use experimental derivative check, below
        disp('Warning: Upper and lower amplitudes are effectively equal:')
        disp(['       ' char(inputname(1)) ' and ' char(inputname(2)) ' at row ' num2str(rowcount) '.'])
        disp('       Cannot calculate amplitude methods: writing NaN.')
        fluxes(rowcount,1)=NaN;
        fluxes(rowcount,3)=NaN;
        if isempty(nopause)
            nopause=input('Press ENTER to continue, or type 1 then ENTER to suppress all further pauses: ');
        end %if nopause
    else  % Calculate Amplitude methods:
        
        %%%%%%%%%% HATCH AMPLITUDE METHOD %%%%%%%%%%
        
        % Equation 6a from Hatch et al. 2006 with alpha substituted and beta (dispersivity) term added to Ke.
        % v(Ar) is moved to the right side, so equation equals zero.
        % The command 'v_min=@(v)' is a 'function_handle', MATLAB syntax
        % for an anonymous function, known as v_min, in terms of v. The function follows.
        v_min = @(v) (2*(Ke+abs(beta*v))/z)*log(Ar)+sqrt(((sqrt(v^4+(8*pi()*(Ke+abs(beta*v))/P)^2))+v^2)/2)-v;   %+ all Ke+beta*v --> Ke+abs(beta*v)
        
        % Run 'fzero' to solve function v_min by finding the value of v (closest to v=0) at which v_min changes sign.
        try
            thermal_front_velocity= fzero(@(v) v_min(v),0);
        catch %in case fzero throws an error that fxn is undefined at 0
            try
                thermal_front_velocity= fzero(@(v) v_min(v),10^-6);
            catch
                thermal_front_velocity=NaN;
            end %2nd try
        end %1st try
        
        % Calculate seepage flux, q, in m/s.
        seepage_flux_m_per_second = thermal_front_velocity*heat_capacity_ratio/60/60;
                
        % Hatch Amplitude derivative check (from Hatch et al. 2006, section 3.1).  Enable/disable this section with the option at the beginning of vflux.m.
        if ~isnan(thermal_front_velocity) && evalin('caller','exist(''dArdq_limit'',''var'')') %if flux is not NaN, and dArdq_limit exists in the caller
            % Check to see if derivative dAr/dq is too low for reliable calcs (see Hatch et al. 2006, paragraph 25)
            % Note: The equation for dArdv was found using 'diff' function in symbolic toolbox.
            v=thermal_front_velocity; %thermal front velocity (v), not seepage flux (q)
            dArdv=-exp((z*(v - (1/2*(v^4 + 64/P^2*pi^2*(Ke + abs(beta*v))^2)^(1/2) + 1/2*v^2)^(1/2)))/(2*Ke + 2*abs(beta*v)))*((z*((v + (4*v^3 + (128*pi^2*abs(beta)*(Ke + abs(beta*v)))/P^2)/(4*(v^4 + (64*pi^2*(Ke + abs(beta*v))^2)/P^2)^(1/2)))/(2*((v^4 + (64*pi^2*(Ke + abs(beta*v))^2)/P^2)^(1/2)/2 + v^2/2)^(1/2)) - 1))/(2*Ke + 2*abs(beta*v)) + (2*abs(beta)*z*(v - (1/2*(v^4 + 64/P^2*pi^2*(Ke + abs(beta*v))^2)^(1/2) + 1/2*v^2)^(1/2)))/(2*Ke + 2*abs(beta*v))^2); %+
            dArdq_limit=evalin('caller','dArdq_limit'); %get dArdq_limit value from caller function vflux.m (in d/m)
            if dArdv<dArdq_limit*24*heat_capacity_ratio  %change deriv. limit from value in terms of seepage flux (q), in d/m, to value in terms of thermal front velocity (v), in h/m
                disp('Warning: Derivative dAr/dq is below the cutoff limit for reliable calculation.')
                disp('       (see Hatch et al. 2006, para. 25)')
                disp('       Note that this optional check can be disabled by a switch in the code of vflux.m.')
                disp('       Writing NaN for Hatch Amplitude method.')
                if isempty(nopause)
                    nopause=input('Press ENTER to continue, or type 1 then ENTER to suppress all further pauses: ');
                end %if nopause
                seepage_flux_m_per_second=NaN;
            end %if
        end %if for derivative check
        
        % Write Hatch amplitude flux to column 1 of results matrix.
        fluxes(rowcount,1)=seepage_flux_m_per_second;
        
        %%%%%%%%%% KEERY AMPLITUDE METHOD %%%%%%%%%%
        
        % Equation 9 from Keery et al. 2007.
        H=Cw/K;  %H term in Eq. 9
        D=log(Ar);  %D term in Eq. 9
        % Equation is a third-order polynomial that equals zero, so solve with roots function.
        qroots=roots([H^3*D/4/z, -5*H^2*D^2/4/z^2, 2*H*D^3/z^3, (pi*C/K/P)^2-(D^4/z^4)]);
        
        % If one real root, write as seepage_flux_m_per_hr; otherwise, write NaN.
        realcheck=[isreal(qroots(1));isreal(qroots(2));isreal(qroots(3))]; %logical matrix, 1 for real and 0 for complex
        if sum(realcheck)==1 %if only 1 real root
            seepage_flux_m_per_hr=qroots(realcheck); %write flux as the real root
        else
            seepage_flux_m_per_hr=NaN; %write as NaN if 3 real roots (or none found)
        end %if
      
        seepage_flux_m_per_second=seepage_flux_m_per_hr/60/60; %write flux in m/s
        
        % Write Keery amplitude flux to column 3 of results matrix.
        fluxes(rowcount,3)=seepage_flux_m_per_second;
        
    end %IF block for amp methods
    
    % Display error and write NaNs if timelag is NaN or close to zero
    if isnan(timelag) || timelag<=0  % Increase this number to cut off artificially high flux rates due to error
        disp('Warning: Phase difference is zero or negative:')
        disp(['       ' char(inputname(3)) ' and ' char(inputname(4)) ' at row ' num2str(rowcount) '.'])
        disp('       Cannot calculate phase methods: writing NaN.')
        fluxes(rowcount,2)=NaN;
        fluxes(rowcount,4)=NaN;
        if isempty(nopause)
            nopause=input('Press ENTER to continue, or type 1 then ENTER to suppress all further pauses: ');
        end %if nopause
    else  % Calculate Phase methods:
    
        %%%%%%%%%% HATCH PHASE METHOD %%%%%%%%%%
        
        % Equation 6b from Hatch et al. 2006, with alpha substituted and betta term added to Ke.
        % v(timelag) is moved to the right side, so equation equals zero.
        % Solve like in Hatch Amplitude Method, above.
        v_min = @(v) sqrt(sqrt(v^4+(8*pi()*(Ke+abs(beta*v))/P)^2)-2*(timelag*4*pi*(Ke+abs(beta*v))/P/z)^2)-v;
        try
            thermal_front_velocity=fzero(@(v) v_min(v),0);
        catch %in case fzero throws an error
            try
                thermal_front_velocity=fzero(@(v) v_min(v),10^-6);
            catch
                try
                    thermal_front_velocity=fzero(@(v) v_min(v),1);
                catch
                    thermal_front_velocity=NaN;
                end %3rd try
            end %2nd try
        end %1st try
        seepage_flux_m_per_second = thermal_front_velocity*heat_capacity_ratio/60/60;
        
        % If real, write Hatch phase flux to column 2 of results matrix.
        if isreal(seepage_flux_m_per_second)==1
            fluxes(rowcount,2)=seepage_flux_m_per_second;
        else fluxes(rowcount,2)=NaN;  %if not real, write NaN
        end
        
        %%%%%%%%%% KEERY PHASE METHOD %%%%%%%%%%
        
        % Equation 11 from Keery et al. 2007.
        seepage_flux_m_per_hr = sqrt((C*z/Cw/timelag)^2-(K*4*pi*timelag/Cw/P/z)^2);
        seepage_flux_m_per_second=seepage_flux_m_per_hr/60/60;
        
        % If real, write Keery phase flux to column 4 of results matrix.
        if isreal(seepage_flux_m_per_second)==1
            fluxes(rowcount,4)=seepage_flux_m_per_second;
        else fluxes(rowcount,4)=NaN;  %if not real, write NaN
        end
    
    end %IF block for phase methods 

    % Luce and McCallum methods. These are direct solutions using amplitude ratio and phase shift     %+
    %%%%%%%%%% McCALLUM METHODS %%%%%%%%%%                        %+
    % As a reminder col 7=McCalq, 8=McCalKe,  9=Luceq 10=LuceKe   %+  
    
    if Ar > 1.0 || timelag <= 0.0 % Don't perform McCallum/Luce calculations if Ar exceeds one, OR phase is negative
        disp('Warning: phase <0, or Ar >1, no calculations for McCallum/Luce methods ')
        disp(['       ' char(inputname(3)) ' and ' char(inputname(4)) ' at row ' num2str(rowcount) '.'])
        disp('       Cannot calculate q, Ke or dz: writing NaN.')
        fluxes(rowcount,7)=NaN;
        fluxes(rowcount,8)=NaN;
        fluxes(rowcount,9)=NaN;
        fluxes(rowcount,10)=NaN;        
        fluxes(rowcount,11)=NaN;     
        
    else % perform calculations for McCallum/Luce methods    
        
        % McCallum et al. (2012) Equation 11 
        seepage_flux_m_per_second = -heat_capacity_ratio*((z*(((P*3600)*(P*3600)*log(Ar)*log(Ar))-(4.0*(pi^2.0)*((timelag*3600.0)^2.0))))/((timelag*3600.0)*(sqrt((16.0*(pi^4.0)*((timelag*3600.0)^4.0))+(8.0*((P*3600)^2.0)*(pi^2.0)*((timelag*3600.0)^2.0)*((log(Ar))^2.0))+((((P*3600)^4.0)*(log(Ar))^4.0))))));
        fluxes(rowcount,7)=seepage_flux_m_per_second;

        % McCallum et al. (2012) Equation 12
        KeM_m2_per_second =  (((z^2.0)*((P*3600.0)^2.0) *log(Ar)) *  ((4.0* (pi^2.0)*((timelag*3600.0)^2.0))-((((P*3600))^2.0)*((log(Ar))^2.0))))  /  ((timelag*3600.0)* (  (((P*3600))^2.0)*((log(Ar))^2.0)  +  (4.0*(pi^2.0)*((timelag*3600.0)^2.0))) * (  (((P*3600))^2.0)*((log(Ar))^2.0)  -  (4.0*(pi^2.0)*((timelag*3600.0)^2.0)))          );
        fluxes(rowcount,8)=KeM_m2_per_second;
   
        %%%%%%%%%% LUCE METHODS %%%%%%%%%%                                       %+
        % Luce et al. (2013) Equation 64d
        eta = -log(Ar)/phaselag;
        omega = (2.0*pi)/(P*3600.0);
        
        seepage_flux_m_per_second = heat_capacity_ratio*  (((2*pi)/((P*3600))*z)/phaselag )*(((1.0- ((-log(Ar)/phaselag)^2.0)  )/   (1.0 + ((-log(Ar)/phaselag)^2.0))));
        fluxes(rowcount,9)=seepage_flux_m_per_second;
    
        % Luce et al. (2013) Equation 64c
        KeL_m2_per_second = (((2.0*pi)/(P*3600))*(z^2.0)) / ( (phaselag^2.0) * (   (1.0/((-log(Ar)/phaselag))     ) + ((-log(Ar)/phaselag))       )    )           ;
        fluxes(rowcount,10)=KeL_m2_per_second;                                                  %+

        % Luce et al. (2013) Equation 57 for scour              
        dzl = (sqrt((2.0* (Ke/3600.0))/(omega)))   *sqrt(  ((log(Ar)*log(Ar))+(phaselag^2.0))/ (2.0*((eta)))    ) ;
        fluxes(rowcount,11)=dzl;
    end % McCallum and Luce methods
    
end %FOR ROWCOUNT loop to calculate fluxes

if evalin('caller','exist(''vfluxversion'')') %if called by vflux (i.e. if vfluxversion exists in the caller workspace)
    assignin('caller','nopause',nopause); %assign nopause as a variable in caller (vflux.m) workspace
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