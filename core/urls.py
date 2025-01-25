from django.urls import path
from .views import UserCreateAPIView, UserLoginAPIView, BidCreateView, AcceptBidView, NotificationListView, MarkNotificationAsReadView, ClientJobListView, ClientJobCreateView, BidDetailView
from .views import GetQuoteView, JobSearchView, ProjectListView, ProjectDetailView, FileDetailView, JobListView, AccessorJobView, JobsAndBidsView, AssessmentView, AssessmentQuoteView, UpdateUserView
from .views import TotalAccessorsView, TotalClientsView, TotalPendingJobsView, ACDetailsView, ClientDetailView, AdminJobAndQuoteView, ListAccessorBidsView, PlaceBidView, MyBidsView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('notifications/', NotificationListView.as_view(), name='notification-list'),

    path('notifications/<int:notification_id>/mark-as-read/', MarkNotificationAsReadView.as_view(), name='mark-as-read'),

                                                #HOME PAGE
    path('create/', UserCreateAPIView.as_view(), name='user-create'),

    path('signin/', UserLoginAPIView.as_view(), name = 'user-login'),

    path('get-quote/', GetQuoteView.as_view()),  # For GET request to create a new instance

    path('get-quote/<int:pk>/', GetQuoteView.as_view()),  # For PUT request to update an instance



                                            #HOME OWNER SCREEN
    path('client/jobs/', ClientJobListView.as_view(), name='client-job-list'), #list all the jobs made by client

    path('client/jobs/create/', ClientJobCreateView.as_view(), name='client-job-create'), #lets the authenticated user create a job id with a get request

    path('job/<int:job_id>/update/', ClientJobCreateView.as_view(), name='client-job-add'), #for updating the job attributes

    path('client/jobs/<int:pk>/', ClientJobListView.as_view(), name='client-job-update'),  # For updating job status by pk

    path('job-search/', JobSearchView.as_view(), name='job-search'), #lets search jobs according to parameters

    path('jobs-bids/', JobsAndBidsView.as_view(), name='client-jobs-and-bids'), ###jobs-bids will all the jobs that have some bid or quote on them

    path('bids/<int:bid_id>/', BidDetailView.as_view(), name='bid-detail'), ##seee the bid details ######(THIS SAME ENDPOINT WILL BE USED FOR REQUOTEING IN THE MY MQUOTES ACCESSIR VIEW USING THE QUOTE ID)

    path('bids/<int:bid_id>/accept/', AcceptBidView.as_view(), name='accept-bid'), #send post request to accept bid




                                            #ACCESSORS SCREENS
    path('jobs/', AccessorJobView.as_view(), name='job-accessor'), ####list all the jobs that or quotes that have a pending status

    path('quotes/<int:quote_id>/bid/', PlaceBidView.as_view(), name='place-bid'), ###for placing a bid on quote instead of job

    path('my-quotes/', MyBidsView.as_view(), name='accessor_bids'), #### Will list jobs that he had placed bids on

    path('my-clients/', ListAccessorBidsView.as_view(), name='my-clients'), ###list the clients that are associated with the accessor

    path('jobs/<int:job_id>/bid/', BidCreateView.as_view(), name='place-bid'), ### see jobs and bids on them

    path('projects/', ProjectListView.as_view(), name='project-list'), ### will list the job with its assesment id

    # URL for viewing a specific project by its ID
    path('projects/<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),

    path('assessment/', AssessmentView.as_view(), name='create-assessment'), ### will generate an assesment id

    path('assessment/<int:assessment_id>/', AssessmentView.as_view(), name='update-assessment'), ### endpoint to updating the attributs of accesment

    path('assess/<int:assessment_id>/', AssessmentQuoteView.as_view(), name='assessment-update'), ##### endpoint for using a quote id to add assesment for get quote ber certificate

    path('preference/', UpdateUserView.as_view(), name='update-preference'), ### endpoint for setting the preference



                                            # ADMIN SCREEN
    path('admin/total-accessors/', TotalAccessorsView.as_view(), name='total-accessors'), ### list the total number of accessors

    path('admin/total-clients/', TotalClientsView.as_view(), name='total-clients'), ### lists the total number of clients

    path('admin/total-pending-jobs/', TotalPendingJobsView.as_view(), name='total-pending-jobs'), ### lists the total pending jobs

    path('admin/clients/', ACDetailsView.as_view(), name='admin-clients'), #### the all the clients with their details

    path('client/<int:id>/', ClientDetailView.as_view(), name='admin-c-data'), ##### lists the clients individualy

    path('admin/ejobs/', AdminJobAndQuoteView.as_view(), name='admin-job-and-quote'), #lists all the active jobs/quotes with pending status

    ##### BER MEMBER VIEW MISSING ######### DONT EXACTLY KNOW WHAT THIS IS ############################

    ################### NOT BEING USED #######################

    path('all-jobs/', JobListView.as_view(), name='all-jobs'), #### will list all the jobs (need checking) (not being used any where)

    path('projects/<int:project_id>/files/', FileDetailView.as_view(), name='file-upload-list'), ### Optional for uploading files on the relating to the project
    # POST for file upload, GET for file list
    path('files/<int:pk>/', FileDetailView.as_view(), name='file-detail'),  ### GET, PUT, DELETE for file details, (not being used anywhere)

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
