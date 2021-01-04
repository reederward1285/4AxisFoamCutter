#!/bin/bash
set -e

. /etc/os-release || { echo "Error: Cannot determine which distribution you are running."; exit 1; }

if [[ -z "$1" ]]; then
    echo "This scripts installs build and runtime dependencies for Inkscape."
    echo "Usage:"
    echo "$0 --minimal       absolute minimum of packages for compiling and running inkscape"
    echo "$0 --recommended   recommended set of packages, including optional build and runtime dependencies (including extensions and testing)"
    echo "$0 --full          everything that may be useful, including utilities for the automatic build infrastructure, such as static code analysis"
    exit 1
fi

# Parse parameters - see the above help message
EXTRA_DEPENDENCIES="true" # --full: install rarely needed utilities for the automatic build infrastructure, such as static code analysis
RECOMMENDED_DEPENDENCIES="true" # --recommended or --full: install optional dependencies for build, runtime and testing
if [[ "$1" == "--minimal" ]]; then
    EXTRA_DEPENDENCIES="false"
    RECOMMENDED_DEPENDENCIES="false"
elif [[ "$1" == "--recommended" ]]; then
    EXTRA_DEPENDENCIES="false"
    RECOMMENDED_DEPENDENCIES="true"
elif [[ "$1" == "--full" ]]; then
    EXTRA_DEPENDENCIES="true"
    RECOMMENDED_DEPENDENCIES="true"
else
    # show help by calling this script again without parameters
    "$0"
fi


# Test if 'sudo' is available, work around otherwise
if ! which sudo > /dev/null; then
    # sudo is not available
    if [[ "$EUID" == "0" ]]; then
        # we are running as root. use a dummy function so that 'sudo command' just calls 'command'.
        function sudo() {
            $@
        }
    else
        echo "Please run this script as root."
        exit 1
    fi
fi

echo "Downloading and installing dependencies. This may take some time."

set -x # print all run commands to help troubleshooting

######################################
# Debian, Ubuntu
# and derived distributions
######################################
if [[ "$ID" == "debian" || "$ID" == "ubuntu" \
    || "$ID_LIKE" == *"debian"* || "$ID_LIKE" == *"ubuntu"* ]]; then
    sudo apt-get update -yqq
    sudo apt-get install -y -qq \
        build-essential \
        cmake \
        intltool \
        pkg-config \
        python3-dev \
        libtool \
        ccache \
        doxygen \
        git
    if $EXTRA_DEPENDENCIES; then
        # Dependencies which are rarely needed, except for continuous integration:
        # Static code analysis and formatting check using clang
        sudo apt-get install -y -qq \
            clang \
            clang-format \
            clang-tidy \
            jq
        # missing clang-tidy dependency (https://bugs.launchpad.net/ubuntu/+source/llvm-toolchain-6.0/+bug/1810298)
        sudo apt-get install -y -qq python-yaml
        # For Debian stretch, the package "clang-tools" is called "clang-tools-4.0".
        sudo apt-get install -y -qq clang-tools || sudo apt-get -y -qq install clang-tools-4.0
    fi
    sudo apt-get install -y -qq \
        wget \
        software-properties-common \
        libart-2.0-dev \
        libaspell-dev \
        libblas3 \
        liblapack3 \
        libboost-dev \
	libboost-filesystem-dev \
        libboost-python-dev \
        libcdr-dev \
        libdouble-conversion-dev \
        libgc-dev \
        libgdl-3-dev \
        libglib2.0-dev \
        libgsl-dev \
        libgtk-3-dev \
        libgtkmm-3.0-dev \
        libgspell-1-dev \
        libgtkspell3-3-dev \
        libhunspell-dev \
        libjemalloc-dev \
        liblcms2-dev \
        libmagick++-dev \
        libpango1.0-dev \
        libpng-dev \
        libpoppler-glib-dev \
        libpoppler-private-dev \
        libpotrace-dev \
        libreadline-dev \
        librevenge-dev \
        libsigc++-2.0-dev \
        libsoup2.4-dev \
        libvisio-dev \
        libwpg-dev \
        libxml-parser-perl \
        libxml2-dev \
        libxslt1-dev \
        python-lxml \
        zlib1g-dev
    if $RECOMMENDED_DEPENDENCIES; then
        # Test tools, optional but recommended
        sudo apt-get install -y -qq \
            google-mock \
            imagemagick \
            libgtest-dev \
            fonts-dejavu || echo "Installation of optional test tools failed. Building should still work."
        # Build google tests on CI (fixes poor packaging in 18.04)
        if [[ -n "$CI" &&  "$VERSION_ID" == "18.04"  &&  "$ID" == "ubuntu" ]]; then
            mkdir /tmp/build-gtest
            (cd /tmp/build-gtest; cmake /usr/src/googletest -DCMAKE_INSTALL_PREFIX=/usr ; sudo cmake --build . --target install)
            rm -rf /tmp/build-gtest
        fi
    fi
    if $RECOMMENDED_DEPENDENCIES; then
        # Recommended runtime dependencies, optional
        sudo apt-get install -y -qq \
            aspell \
            imagemagick \
            libwmf-bin \
            perlmagick \
            python3-pip \
	    cython \
            python3-numpy \
            python3-lxml \
            python3-serial \
            python3-scour \
            adwaita-icon-theme-full  || echo "Installation of optional (recommended) dependencies failed. Building will still work. Some extensions may not run."
        # python-uniconvertor is recommended, but not available in Ubuntu 18.04. We hope it will reappear one day.
        sudo apt-get install -y -qq python-uniconvertor || true
    fi
    if  "$RECOMMENDED_DEPENDENCIES"  && [[ -z "$CI" &&  "$VERSION_ID" == "18.04" && "$ID" == "ubuntu" ]]; then
      echo "
      WARNING: Google Test package in Ubuntu 18.04 does not contain binaries
               Run the following commands to build & install Google Test from sources:

            mkdir /tmp/build-gtest
            cd /tmp/build-gtest
            cmake /usr/src/googletest -DCMAKE_INSTALL_PREFIX=/usr
            sudo cmake --build . --target install
            rm -rf /tmp/build-gtest
       "
    fi

######################################
# Fedora
######################################
elif [[ "$ID" == "fedora" || "$ID_LIKE" == *"fedora"* ]]; then
    sudo dnf builddep inkscape
    sudo dnf -y install \
        ccache \
        make \
        libsoup-devel \
        double-conversion-devel \
        gtk3-devel \
        gtkmm30-devel \
        gdlmm-devel \
        gspell-devel \
        gtkspell3-devel \
        gmock \
        gmock-devel \
        gtest-devel \
        ImageMagick \
        libcdr-devel \
        libvisio-devel \
        jemalloc-devel \
        readline-devel
    if $RECOMMENDED_DEPENDENCIES; then
        sudo dnf -y install \
            aspell \
            ImageMagick \
            libwmf \
            ImageMagick-perl \
            python-pip \
	    python3-Cython \
            python-numpy \
            python-lxml \
            python-pyserial \
            python-scour \
            adwaita-icon-theme \
            uniconvertor || echo "Installation of optional (recommended) dependencies failed. Building will still work. Some extensions may not run."
    fi
    if $EXTRA_DEPENDENCIES; then
        echo # TODO: install clang, clang-tools
    fi

######################################
# MSYS2 on Windows
######################################
elif [[ "$OSTYPE" == "msys" ]]; then
    echo "Please see the Windows build instructions at http://wiki.inkscape.org/wiki/index.php/Compiling_Inkscape_on_Windows"
    exit 1
    
#####################################
# Arch Linux, Manjaro
#####################################
elif [[ "$ID" == "arch" || "$ID_LIKE" == *"arch"* ]]; then
    sudo pacman -Syu --quiet
    sudo pacman -S --quiet --noconfirm \
        base-devel \
        cmake \
        intltool \
        ccache \
        doxygen \
        git
    if $EXTRA_DEPENDENCIES; then
        # Dependencies which are rarely needed, except for continuous integration:
        # Static code analysis and formatting check using clang
        sudo pacman -S --quiet --noconfirm \
            clang
        # clang installs both clang-tidy, clang-format and clang-tools
        sudo pacman -S --quiet --noconfirm \
            python-yaml
    fi
    sudo pacman -S --quiet --noconfirm \
        wget \
        aspell \
        blas \
        lapack \
        boost \
        libcdr \
        double-conversion \
        gc \
        gdl \
        glib2 \
        gsl \
	gspell \
        gtk3 \
        gtkmm3 \
        gtkspell3 \
        hunspell \
        jemalloc \
        lcms2 \
        imagemagick \
        pango \
        libpng \
        poppler-glib \
        poppler \
        potrace \
        readline \
        librevenge \
        libsigc++ \
        libsoup \
        libvisio \
        libwpg \
        perl-xml-parser \
        libxml2 \
        libxslt \
        python-lxml \
        zlib

    if $RECOMMENDED_DEPENDENCIES; then
        # Test tools, optional but recommended
        sudo pacman -S --quiet --noconfirm \
            gtest \
            ttf-dejavu \
            libwmf \
            python-pip \
	    cython \
            python-numpy \
            python-lxml \
            python-pyserial \
            scour \
            adwaita-icon-theme
    fi
    
######################################
# example for adding a new distribution
######################################
elif [[ "$ID" == "/etc/os-release ID of my favourite linux distribution" ]]; then
    # add your commands here
    echo "do something"

######################################
# Error handling
######################################
else
    echo "Error: Sorry, we don't have instructions for your distribution yet. Please contribute on https://inkscape.org/contribute/report-bugs/ ."
    exit 1
fi

echo "Done."
