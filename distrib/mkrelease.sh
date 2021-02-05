#!/bin/bash
#
# Create a Labtainers release.  
# --Merge premaster into master
# --Update the release information in the README file.
# --Tag the current commit and push the release artifacts.
#
if [[ -z "$1" ]]; then
    tag=$(git tag | tail -n 1)
    echo "Missing tag, most recent is "$tag" .  Pick the next revision."
    exit
fi
if [[ -z "$gitpat" ]]; then
    echo "gitpat is not defined.  Source the gitpat.sh file"
    exit
fi
if [[ -z "$SSH_AGENT_PID" ]]; then
    echo "No ssh-agent running.  Source ~/agent.sh"
    exit
fi
new_tag=$1
shift 1
here=`pwd`
revision=$new_tag
commit=`git describe --always`
sed -i "s/^Distribution created:.*$/Distribution created: $(date '+%m\/%d\/%Y %H:%M')<\/br>/" ../README.md
sed -i "s/^Revision:.*$/Revision: $revision<\/br>/" ../README.md
sed -i "s/^Commit:.*$/Commit: $commit<\/br>/" ../README.md
sed -i "s/^Branch:.*$/Branch: master<\/br>/" ../README.md
git commit ../README.md -m "Update readme date/rev"
./mergePre.sh $1
git tag $new_tag
#git push --set-upstream origin master
git push --tags

# create the end-user distibution
./mkdist.sh -r || exit 1

# copy end-user distribution files to artifacts
mkdir -p artifacts
cp labtainer.tar artifacts/
cp labtainer_pdf.zip artifacts/
echo "Artifacts for revision $revision" > artifacts/README.txt

echo "Build GUI Jar"
cd $LABTAINER_DIR/UI/bin
./buildUI2.sh -n || exit
cp MainUI.jar $LABTAINER_DIR/distrib/artifacts/
cd $here
echo "Now generate release"
github-release release --security-token $gitpat --user mfthomps --repo Labtainers --tag $new_tag

echo "Upload tar"
github-release upload --security-token $gitpat --user mfthomps --repo Labtainers --tag $new_tag --name labtainer.tar --file artifacts/labtainer.tar
echo "Upload PDF zip"
github-release upload --security-token $gitpat --user mfthomps --repo Labtainers --tag $new_tag --name labtainer_pdf.zip --file artifacts/labtainer_pdf.zip
echo "Upload UI"
github-release upload --security-token $gitpat --user mfthomps --repo Labtainers --tag $new_tag --name MainUI.jar --file artifacts/MainUI.jar