function [output]=vfluxsens(sinput,rfactor,window,Pf,n,beta,Kcal,Cscal,Cwcal)
%
% VFLUXSENS - VFLUX sensitivity analysis program
%
% Description:
%   Does a basic sensitivity analysis on thermal data formatted with
%   VFLUXFORMAT and plots results.  Each input parameter is input as a
%   triplet of low, medium (base), and high values.  The program calculates
%   the range of flux using the range of each individual parameter (low and
%   high), while holding all others at their base values.
%
% Usage:
%   output = vfluxsens(input, rfactor, window, Pf, n, beta, Kcal, Cscal, Cwcal)
%
% Input:
%   Same as vflux.m, except only one window value can be entered, and n,
%   beta, Kcal, Cscal, and Cwcal are entered as triplet vectors, like [1, 2, 3],
%   which represent the low, medium, and high values.
%
% Output:
%   Same as vflux.m, except that many vflux output structures are created,
%   all in one master structure.  Each sub-structure contains a single
%   vflux run for a particular combination of parameters.  The
%   sub-structures are named as follows:
%    output.basevals - the vflux run with all medium (base) values
%    output.lown - vflux run with all base values except the high value for porosity (n)
%    output.highn - etc, except the low value for porosity
%    output.lowbeta - etc.
%    ...etc. for all of the variable parameters
%
% Example:
%   profile01 = vfluxsens(profile01, 0, 3, 1, [0.2 0.28 0.35], [0 0.001 0.01], [0.0029 0.0045 0.0059], [0.4 0.5 0.6], [0.9 1 1.01])
%  [  output  = vfluxsens(input, rfactor, window, Pf, n, beta, Kcal, Cscal, Cwcal) ]
%

% Written by Ryan Gordon, Syracuse University, October 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 103, updated 11/07/2011

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
    error('n, beta, Kcal, Cscal, and Cwcal must all be 3-element vectors.')
elseif length(n)~=3 || length(beta)~=3 || length(Kcal)~=3 || length(Cscal)~=3 || length(Cwcal)~=3
    error('n, beta, Kcal, Cscal, and Cwcal must all be 3-element vectors.')
end %if

% Run vlux.m for middle (base) values, then for high and low values of each parameter with other parameters kept at base values
basevals=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(2),Cscal(2),Cwcal(2),'unattended');
lown=vflux(sinput,rfactor,window,Pf,n(1),beta(2),Kcal(2),Cscal(2),Cwcal(2),'unattended');
highn=vflux(sinput,rfactor,window,Pf,n(3),beta(2),Kcal(2),Cscal(2),Cwcal(2),'unattended');
lowbeta=vflux(sinput,rfactor,window,Pf,n(2),beta(1),Kcal(2),Cscal(2),Cwcal(2),'unattended');
highbeta=vflux(sinput,rfactor,window,Pf,n(2),beta(3),Kcal(2),Cscal(2),Cwcal(2),'unattended');
lowKcal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(1),Cscal(2),Cwcal(2),'unattended');
highKcal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(3),Cscal(2),Cwcal(2),'unattended');
lowCscal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(2),Cscal(1),Cwcal(2),'unattended');
highCscal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(2),Cscal(3),Cwcal(2),'unattended');
lowCwcal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(2),Cscal(2),Cwcal(1),'unattended');
highCwcal=vflux(sinput,rfactor,window,Pf,n(2),beta(2),Kcal(2),Cscal(2),Cwcal(3),'unattended');

% Write structures to output
output.basevals=basevals;
output.lown=lown;
output.highn=highn;
output.lowbeta=lowbeta;
output.highbeta=highbeta;
output.lowKcal=lowKcal;
output.highKcal=highKcal;
output.lowCscal=lowCscal;
output.highCscal=highCscal;
output.lowCwcal=lowCwcal;
output.highCwcal=highCwcal;

% Make plots
while 1 %loop forever until return or break encountered
    disp(' ')
    disp('Would you like to make sensitivity plots?  For which method?')
    disp('  1) Hatch Amplitude')
    disp('  2) Keery Amplitude')
    disp('  3) Hatch Phase')
    disp('  4) Keery Phase')
    disp('  5) McCallum/Luce')
    disp('  6) EXIT')
    method=input('Select a menu number: ');
    if method==6, return %end function
    elseif isempty(method), continue %re-ask question if nothing entered
    elseif method~=1 && method~=2 && method~=3 && method~=4 && method~=5,continue %re-ask question if entered incorrectly
    end %if
    switch method %switch sets which flux matrix to pull from each structure, depending on method chosen
        case 1, fluxmat='fluxha';
        case 2, fluxmat='fluxka';
        case 3, fluxmat='fluxhp';
        case 4, fluxmat='fluxkp';
        case 5, fluxmat='fluxm';    
    end %switch
    copdepths=output.basevals.fluxinfo(4,:); %get center-of-pair depths
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
        
        subplot(2,3,1) %plot n
        hold on
        eval(['plot(output.lown.dtime,output.lown.' fluxmat '(:,pair),''g'')'])
        eval(['plot(output.basevals.dtime,output.basevals.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.highn.dtime,output.highn.' fluxmat '(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.basevals.dtime(1),output.basevals.dtime(end)]) %set x-axis limits to time range
        title('Porosity'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend(num2str(n(1)),num2str(n(2)),num2str(n(3))); %legend of values (base,high,low)
        
        subplot(2,3,2) %plot beta
        hold on
        eval(['plot(output.lowbeta.dtime,output.lowbeta.' fluxmat '(:,pair),''g'')'])
        eval(['plot(output.basevals.dtime,output.basevals.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.highbeta.dtime,output.highbeta.' fluxmat '(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.basevals.dtime(1),output.basevals.dtime(end)]) %set x-axis limits to time range
        title('Dispersivity (m)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend(num2str(beta(1)),num2str(beta(2)),num2str(beta(3))); %legend of values (base,high,low)
        
        subplot(2,3,3) %plot Kcal
        hold on
        eval(['plot(output.lowKcal.dtime,output.lowKcal.' fluxmat '(:,pair),''g'')'])
        eval(['plot(output.basevals.dtime,output.basevals.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.highKcal.dtime,output.highKcal.' fluxmat '(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.basevals.dtime(1),output.basevals.dtime(end)]) %set x-axis limits to time range
        title('Thermal Conductivity (cal/s-cm-C)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend(num2str(Kcal(1)),num2str(Kcal(2)),num2str(Kcal(3))); %legend of values (base,high,low)
        
        subplot(2,3,4) %plot Cscal
        hold on
        eval(['plot(output.lowCscal.dtime,output.lowCscal.' fluxmat '(:,pair),''g'')'])
        eval(['plot(output.basevals.dtime,output.basevals.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.highCscal.dtime,output.highCscal.' fluxmat '(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.basevals.dtime(1),output.basevals.dtime(end)]) %set x-axis limits to time range
        title('Heat Capacity Sediment (cal/cm^3-C)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend(num2str(Cscal(1)),num2str(Cscal(2)),num2str(Cscal(3))); %legend of values (base,high,low)
        
        subplot(2,3,5) %plot Cwcal
        hold on
        eval(['plot(output.lowCwcal.dtime,output.lowCwcal.' fluxmat '(:,pair),''g'')'])
        eval(['plot(output.basevals.dtime,output.basevals.' fluxmat '(:,pair),''b'')'])
        eval(['plot(output.highCwcal.dtime,output.highCwcal.' fluxmat '(:,pair),''r'')'])
        hold off
        set(gca,'XLim',[output.basevals.dtime(1),output.basevals.dtime(end)]) %set x-axis limits to time range
        title('Heat Capacity Water (cal/cm^3-C)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
        legend(num2str(Cwcal(1)),num2str(Cwcal(2)),num2str(Cwcal(3))); %legend of values (base,high,low)
        
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