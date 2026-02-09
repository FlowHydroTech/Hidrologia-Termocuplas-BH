function [output]=vfluxmc(sinput,rfactor,window,Pf,n,beta,Kcal,Cscal,Cwcal)
%
% VFLUXMC - VFLUX Monte Carlo analysis program
%
% Description:
%   Does a Monte Carlo analysis on thermal data formatted with VFLUXFORMAT
%   and plots results.  Each input parameter is input as a pair of "mean"
%   and "standard deviation" values.  The program first runs vflux once
%   with the "mean" parameter values.  Then it performs 1000 realizations
%   (by default, can be changed in code below), in each of which it selects
%   a set of random parameters from normal distributions given by the input
%   mean and standard deviation and calculates flux through time for these
%   parameters.  Most of the parameters are uncorrelated, except for the
%   thermal conductivity (Kcal) and porosity (n), which are inversely
%   correlated.  The output plot is composed of the flux values through
%   time for the input mean values, and an envelope above and below this
%   line that represents two-times the standard deviation of the flux
%   values calculated from the 1000 simulations.
%   Note: if you run out of memory, close open programs, increase virtual
%   memory, or decrease the number of realizations.
%
% Usage:
%   output = vfluxmc(input, rfactor, window, Pf, n, beta, Kcal, Cscal, Cwcal)
%
% Input:
%   Same as vflux.m, except only one window value can be entered, and n,
%   beta, Kcal, Cscal, and Cwcal are entered as vector pairs, like [3 1]
%   which represent the mean and standard deviation, respectfully.
%
% Output:
%   Same as vflux.m (in this case, the fluxha, fluxhp, etc. arrays are for
%   the "mean" input parameters), plus the following additional arrays
%   in the output structure:
%    montecarlo - stores the parameters that were randomly chosen in each
%        realization.  Each row represents one realization.  Columns are, in
%        order, n, beta, Kcal, Cscal, and Cwcal.
%    fluxhamc - a 3-D array that stores the fluxha array from each Monte
%        Carlo vflux run in its own "page" (in the third dimension).  Each
%        page represents one realization.  Same for fluxhpmc, fluxkamc, and
%        fluxkpmc.
%    fluxhalow - a matrix the same size as fluxha, in which each element
%        (flux estimate for a particular sensor pair at a particular point
%        in time) is the same element from fluxha minus 2 times the
%        standard deviation of that element (2D) from fluxhamc through the
%        third dimension.
%    fluxhahigh - a matrix the same size as fluxha, in which each element
%        (flux estimate for a particular sensor pair at a particular point
%        in time) is the same element from fluxha plus 2 times the standard
%        deviation of that element (2D) from fluxhamc through the third
%        dimension.
%
% Example:
%   profile01 = vfluxmc(profile01, 0, 3, 1, [0.28 0.04], [0.001 0], [0.0045 0.0007], [0.5 0.05], [1 0.005])
%  [  output  = vfluxmc(input, rfactor, window, Pf, n, beta, Kcal, Cscal, Cwcal) ]
%

% Written by Ryan Gordon, Syracuse University, October 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 104, updated 03/13/2015

sims=1000; %number of realizations

% Check input arguments
if nargin~=9
    error('Wrong number of input arguments.')
elseif isfield(sinput,'time')+isfield(sinput,'temp')+isfield(sinput,'depth')~=3
    error('The input structure must contain time, temp, and depth arrays, as created by VFLUXFormat. Please run VFLUXFormat.')
elseif ~isscalar(rfactor) || rfactor<0 || mod(rfactor,1)~=0 %if rfactor is not a scalar positive integer
    error('rfactor must be a positive integer.')
elseif ~isscalar(window) || any(window<1) || any(mod(window,1)~=0) %if window is not a scalar positive integer
    error('VFLUXSENS can only be run with one window: window must be a scalar positive integer.')
elseif ~isscalar(Pf)
    error('Pf must be a scalar.')
elseif isvector(n)+isvector(beta)+isvector(Kcal)+isvector(Cscal)+isvector(Cwcal)~=5
    error('n, beta, Kcal, Cscal, and Cwcal must all be 2-element vectors.')
elseif length(n)~=2 || length(beta)~=2 || length(Kcal)~=2 || length(Cscal)~=2 || length(Cwcal)~=2
    error('n, beta, Kcal, Cscal, and Cwcal must all be 2-element vectors.')
end %if

% Run VFLUX for mean values
output=vflux(sinput,rfactor,window,Pf,n(1),beta(1),Kcal(1),Cscal(1),Cwcal(1),'unattended'); %call to vflux.m

% Preallocate arrays
output.montecarlo=ones(sims,7); %preallocate montecarlo array (to store parameters of each realization in each row) %+ was 5, 2 extra for Mcallum and Luce q and thermal conductivity calcs
output.fluxhamc=ones([size(output.fluxha),sims]); %preallocate 3-D flux result arrays (one page for each realization)
output.fluxhpmc=ones([size(output.fluxhp),sims]); %etc.
output.fluxkamc=ones([size(output.fluxka),sims]);
output.fluxkpmc=ones([size(output.fluxkp),sims]);
output.fluxmmc=ones([size(output.fluxm),sims]);  %+ McCallum q calculation
output.fluxlmc=ones([size(output.fluxl),sims]);  %+ Luce q calculation

output.montecarlo(:,:)=NaN; %make all the ones NaNs (just for safety!)
output.fluxhamc(:,:,:)=NaN; %make all the ones NaNs (just for safety!)
output.fluxhpmc(:,:,:)=NaN; %etc.
output.fluxkamc(:,:,:)=NaN;
output.fluxkpmc(:,:,:)=NaN;
output.fluxmmc(:,:,:)=NaN; %+ McCallum q calculation
output.fluxlmc(:,:,:)=NaN; %+ Luce q calculation

% Do Monte Carlo calcs
for i=1:sims
    display(' ')
    display(' ')
    display('**************************************************')
    display(sprintf('  Monte Carlo realization number: %d of %d',i,sims)) %on-screen counter
    display('**************************************************')
    
    % Random number generator --> parameters
    seed=randn(1,4); %get four random numbers from standard normal distribution
    rn=n(1)+seed(1).*n(2); %convert seed(1) into input distribution for n
    rbeta=beta(1)+seed(2).*beta(2); %etc.
    rKcal=Kcal(1)-seed(1).*Kcal(2); %use negative of seed(1) for thermal conductivity, because conductivity is proportional to dry-bulk density (Lapham 1989), which is inversely proportional to porosity
    rCscal=Cscal(1)+seed(3).*Cscal(2);
    rCwcal=Cwcal(1)+seed(4).*Cwcal(2);
    output.montecarlo(i,1:5)=[rn,rbeta,rKcal,rCscal,rCwcal]; % Store parameters in array
    
    % Run VFLUX for realization i and store results
    temp_output=vflux(sinput,rfactor,window,Pf,rn,rbeta,rKcal,rCscal,rCwcal,'unattended'); %call to vflux.m
    output.fluxhamc(:,:,i)=temp_output.fluxha; %store results in output
    output.fluxhpmc(:,:,i)=temp_output.fluxhp; %etc.
    output.fluxkamc(:,:,i)=temp_output.fluxka;
    output.fluxkpmc(:,:,i)=temp_output.fluxkp;
    output.fluxmmc(:,:,i)=temp_output.fluxm; %+ store results for q from the McCallum equation
    output.fluxlmc(:,:,i)=temp_output.fluxl; %+ store results for q from the Luce equation
end %for

% Calculate flux distributions 
fluxhamcmean=mean(output.fluxhamc,3); %get mean flux value of all the realizations at each depth and time (mean through third dimension)
fluxhpmcmean=mean(output.fluxhpmc,3); %etc.
fluxkamcmean=mean(output.fluxkamc,3);
fluxkpmcmean=mean(output.fluxkpmc,3);
fluxmmcmean=mean(output.fluxmmc,3);   %+ McCallum q
fluxlmcmean=mean(output.fluxlmc,3);   %+ Luce q
fluxhamcstdev=std(output.fluxhamc,0,3); %get standard deviation of flux through all the realizations at each depth and time (stdev through third dimension)
fluxhpmcstdev=std(output.fluxhpmc,0,3); %etc.
fluxkamcstdev=std(output.fluxkamc,0,3);
fluxkpmcstdev=std(output.fluxkpmc,0,3);
fluxmmcstdev =std(output.fluxmmc,0,3); %+ added for McCallum q
fluxlmcstdev =std(output.fluxlmc,0,3); %+ added for Luce q
output.fluxhahigh=output.fluxha+2.*fluxhamcstdev; %calculate "high" flux envelope 2 standard deviations above the input mean fluxes
output.fluxhphigh=output.fluxhp+2.*fluxhpmcstdev; %etc.
output.fluxkahigh=output.fluxka+2.*fluxkamcstdev;
output.fluxkphigh=output.fluxkp+2.*fluxkpmcstdev;
output.fluxmhigh=output.fluxm+2.*fluxmmcstdev; %+  McCallum q
output.fluxlhigh=output.fluxl+2.*fluxlmcstdev; %+  Luce q
output.fluxhalow=output.fluxha-2.*fluxhamcstdev; %calculate "low" flux envelope 2 standard deviations below the input mean fluxes
output.fluxhplow=output.fluxhp-2.*fluxhpmcstdev; %etc.
output.fluxkalow=output.fluxka-2.*fluxkamcstdev;
output.fluxkplow=output.fluxkp-2.*fluxkpmcstdev;
output.fluxmlow=output.fluxm-2.*fluxmmcstdev; %+ McCallum q
output.fluxllow=output.fluxl-2.*fluxlmcstdev; %+ Luce q
display(' ')
display(' ')
display(sprintf('VFLUXMC completed %d Monte Carlo realizations.',sims))

% Plot results
while 1 %loop forever until return or break encountered
    disp(' ')
    disp('Would you like to plot results?  For which method?')
    disp('  1) Hatch Amplitude')
    disp('  2) Keery Amplitude')
    disp('  3) Hatch Phase')
    disp('  4) Keery Phase')
    disp('  5) McCallum')
    disp('  6) Luce')
    disp('  7) EXIT')
    method=input('Select a menu number: ');
    if method==7, return %end function
    elseif isempty(method), continue %re-ask question if nothing entered
    elseif method~=1 && method~=2 && method~=3 && method~=4 && method~=5 && method~=6, continue %re-ask question if entered incorrectly
    end %if
    switch method %switch sets which flux matrix to pull from each structure, depending on method chosen
        case 1, fluxmat='fluxha';
        case 2, fluxmat='fluxka';
        case 3, fluxmat='fluxhp';
        case 4, fluxmat='fluxkp';
        case 5, fluxmat='fluxm'; %+  Added for McCallum q                
        case 6, fluxmat='fluxl'; %+  Added for Luce q                        
    end %switch
    copdepths=output.fluxinfo(4,:); %get center-of-pair depths
    while 1 %loop forever until return or break encountered
        disp(' ')
        disp('Choose a pair of sensors to plot:')
        disp('  pair #   mean depth (m)')
        disp([[1:length(copdepths)]',copdepths'])
        pair=input('Please enter the pair number, or ENTER to go back: ');
        if isempty(pair), break, end %break out of inner while loop if 'Exit' is chosen
        if rem(pair,1)~=0 || pair<1 || pair>length(copdepths), continue, end %re-ask question if entered incorrectly
        
        figure %create figure window
        set(gcf, 'Position', get(0,'Screensize')); %maximize figure window
        
        hold on
        eval(['plot(output.dtime,output.' fluxmat 'low(:,pair),''g'')'])
        eval(['plot(output.dtime,output.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.dtime,' fluxmat 'mcmean(:,pair),''--b'')'])
        eval(['plot(output.dtime,output.' fluxmat 'high(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
        title('Monte Carlo Analysis'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend('mean-2\sigma','mean','sample mean','mean+2\sigma');
        
        disp(' Pause for plot: press any key to continue.'), pause %pause for plot
    end %while
end %while

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