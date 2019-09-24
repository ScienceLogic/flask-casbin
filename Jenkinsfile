#!groovy
@Library("composePipeline@1.0.2")__

def notifySlack(text, channel, attachments) {
    //your  slack integration url
    def slackURL = 'https://hooks.slack.com/services/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'
    //from the jenkins wiki, you can updload an avatar and
    //use that one
    def jenkinsIcon = 'https://wiki.jenkins-ci.org/download/attachments/327683/JENKINS?version=1&modificationDate=1302750804000'
    def payload = "{\"text\": \"${text}\", \"channel\": \"${channel}\", \"username\": \"jenkins\", \"icon_url\": \"${jenkinsIcon}\", \"attachments\": ${attachments}}"
    sh "curl -X POST --data-urlencode \'payload=${payload}\' ${slackURL}"
}

node('dockerslave02') {
    def err = null
    def version_used = ''
    def tag = ''
    def content_use_branch = ''
    def repo = ''

    try {
	    stage('Preamble') {
            print "ENV: ${env}"
            print "BUILD_URL: ${env.BUILD_URL}"
            print "JOB_NAME: ${env.JOB_NAME}"
            print "WORKSPACE: ${env.WORKSPACE}"
            print "BRANCH_NAME: ${env.BRANCH_NAME}"
        }
        stage('Checkout') {
            sh 'git config --global http.sslverify false'
            checkout scm

            print "Checkout build repository"
            checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: "master"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'is_build_tools']], gitTool: 'Default', submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'a47b7eb4-3b28-47b9-abb6-18c561796dfa', url: 'ssh://jbitbuck@code.eng.sciencelogic.com/air/is_build_tools']]]
        }
        stage('Versioning and upload wheel') {
            def branch_trimmed = sh(script:"basename ${env.BRANCH_NAME}", returnStdout:true).trim()
            version_used = sh(script:"is_build_tools/autoBuild.sh -b ${branch_trimmed} -w", returnStdout:true).trim()
            print "Wheel created from branch ${branch_trimmed} Uploaded as version: ${version_used}"
        }


    }catch (caught_err) {
        notifySlack("Error building common package or container", "#airlocks-reporting", "[{\"title\": \"${env.JOB_NAME} build ${env.BUILD_NUMBER}\", \"color\":\"warning\", \"text\": \"Build Failure. ${env.BUILD_URL}\"}]")
        throw caught_err
    }
}