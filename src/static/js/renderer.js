(function(window,$){
	Vue.use(VueResource);
	Vue.use(VueRouter);
	
	// const store = new Vuex.store({
	// 	state:{
			
	// 	}
	// });
	$.ajaxSetup({
		type: "POST",
		data: {},
		dataType: 'json',
		xhrFields: {
			withCredentials: true
		},
		crossDomain: true,
		contentType: 'application/json; charset=utf-8'
	});
	
	var self = this;

	this.same_string = (sa, sb) => {
		var f = s => s.replace(/ /g,"");
		return f(sa) == f(sb);
	};
	// self.domain = "https://rubis.limics.upmc.fr";
	// self.domain = "http://localhost:8000";
	// this.build_full_url = url => window.location.href.replace(/#.*$/,"") + url;
	// this.build_full_url = url => "http://localhost:5000/c3-cloud/" + url;
	this.build_full_url = url => "/c3-cloud/" + url;
	
	this.pretty = s => JSON.stringify(s, null, 2);
	
	this.data = {
		codes: [],
		sites: [],
		code_systems: [],
		apikey: "",
		
		headers: [
			{text: "Code", value:"Code", sortable:false, value:false},
			{text: "Code_System", value:"Code_System"},
			{text: "Concept", value:"Concept"},
			{text: "Designation", value:"Designation"}],
		mappings: [],
		dtHandle: null,
		
		tester_from_site: "",
		tester_from_code: "",
		tester_to_site: "",
		getURL: "",
		getResult: "",
		filteredCodes: [],

		initial_mapping_codes_string: "", // """"hash"""" comparison
		concepts: [],
		editor_site: "",
		editor_concept: "",
		editor_codes: {},
		get_mappingURL: "",
		editor_post_url: "",
		editor_post_data: "",
		editor_post_headers: "",
		editor_post_response: ""
	};
	
	// check if a "contenttype" is in the "response"'s headers
	var contentTypeIs = (response, contenttype) =>
		response.headers.get('content-type').indexOf(contenttype) != -1;

	var identity = e => e;

	Vue.component('mapping-editor',{
		template: '#mapping-editor-template',
		data: () => data,
		mounted: function(){
			this.update_editor();
		},
		computed:{
			fields_ok: function(){
				return this.editor_site && this.editor_concept;
			},
			needs_saving: function(){
				console.log("1: " + this.initial_mapping_codes_string);
				console.log("2: " + JSON.stringify(this.codes));
				return this.initial_mapping_codes_string!="" &&
					this.initial_mapping_codes_string !==
					JSON.stringify(this.editor_codes);
			}
		},
		watch: {
			editor_site: function(){
				this.update_editor();
			},
			editor_concept: function(){
				this.update_editor();
			}
		},
		methods:{
			update_editor: function(){
				if(this.fields_ok){
					url = 'mappings/?site='+
						this.editor_site+'&concept='+
						this.editor_concept;
					this.get_mappingURL = self.build_full_url(url);
					
					this.$http.get(this.get_mappingURL).then(response => {
						console.log(response.data.mappings);
						
						this.editor_codes = {};

						response.data.data.forEach((m, i) => {
							this.editor_codes[i] = {};
							this.editor_codes[i].code_system = m.code_system;
							this.editor_codes[i].code_system_uri = m.code_system_uri;
							this.editor_codes[i].code = m.code;
							this.editor_codes[i].designation = m.designation;
						});

						this.initial_mapping_codes_string = JSON.stringify(
							this.editor_codes);
					}, e => console.log("error"));
				}
			},
			add_code: function(){
				console.log("add mapping");
				var n = Object.keys(this.editor_codes).length;
				Vue.set(this.editor_codes, n, {
					code_system: "",
					code: "",
					designation: ""
				});
				console.log(n);
			},
			remove_code: function(i){
				console.log("remove mapping "+i);
				Vue.delete(this.editor_codes, i);
			},
			save_mapping: function(){
				console.log("save mapping");
				var url = "mappings/";
				this.editor_post_url = self.build_full_url(url);

				var codes = Object.values(this.editor_codes).map(function(c){
					c.code_system = {
						code_system: c.code_system,
						uri: c.code_system_uri
					};
					delete c.code_system_uri;
					return( c );
				});

				console.log("codes");
				console.log(codes);
				
				var body = {
					site: this.editor_site,
					concept: this.editor_concept,
					codes: codes
					// key: this.apikey
					// codes: Object.values(this.editor_codes)
				};

				var headers = {'key': this.apikey};
				
				console.log(this.editor_codes);
				this.editor_post_data = pretty(body);
				this.editor_post_headers = pretty(headers);
				this.$http.post(this.editor_post_url,
								body,
								{headers: headers})
					.then(
						(data, status, request) => {
							this.editor_post_response=data.status;
							console.log(data);
						},
						(error) => {
							this.editor_post_response=error.status;
							console.log(error);
						}
					);
			
			}
			
		}
	});

	Vue.component('about',{
		template:'#about-template'
	});
	
	Vue.component('vue-table',{
		template:'#vue-table-template',
		data: () => self.data,
		methods: {
			edit: function(i){
				self.data.editor_site=i['site'];
				self.data.editor_concept=i['concept'];
				
				console.log('emit update_editor_from_table');
				this.$emit('update_editor_from_table');
				
				this.$router.push('mapping-editor');
			}
		}
	});
	
	Vue.component('request-tester', {
		template: '#request-tester-template',
		data: () => data,
		watch:{
			tester_from_site: function(site){
				if (site.length==0) return ;
				var url = ("/c3-cloud/codes/?site=" + site);
				console.log(url);
				this.$http.get(url).then(response => {
					var o = JSON.parse(response.bodyText).data;
					console.log(response.bodyText);
					// console.log('------------------');
					
					// console.log(this.tester_from_site);
					// o = o.filter(e => e.code_system==this.tester_from_site);
					// console.log(o[1]);
					// console.log(o.filter(e => e.code_system==="YOLO"))
					this.filteredCodes = o;
				}, e => {
					console.log("error");
				});
				this.tester_from_code='';
			}
		},
		methods:{
			fields_ok(){
				return this.tester_from_code !== ""
					&& this.tester_from_site !== ""
					&& this.tester_to_site !== "";
			},
			update_tester(){
				if(this.fields_ok()) this.sendRequest();
			},
			sendRequest(){
				// do not use encodeURI 
				// var url = ("translate/?" + $("#get-form").serialize());
				var c = this.filteredCodes.filter(e => self.same_string(this.show_code(e), this.tester_from_code))[0]; // kinda dirty
				// this.filteredCodes.forEach(cc => {
				// 	console.log(cc+" -> ("+this.show_code(cc)
				// 				+")("+this.tester_from_code  +")"
				// 				+ self.same_string(this.show_code(cc), this.tester_from_code))
				// })
				// console.log(c)
				// console.log(this.tester_from_code)
				var url =
					"translate/?"
					+ 'code='
					+ c.code + '&'
					+ 'code_system='
					+ c.code_system_uri + '&'
					+ 'fromSite=' + this.tester_from_site + '&'
					+ 'toSite='   + this.tester_to_site;
				this.getURL = self.build_full_url(url);
			
				var f = response => {
					this.getResult = "";

					this.getResult += "status: " + response.status + "\n";
					this.getResult += "status text: " + response.statusText + "\n";
					
					this.getResult += "\nBody:\n";
					// prettify json
					this.getResult += (contentTypeIs(response, "application/json")?
									   e => self.pretty(JSON.parse(e)):
									   identity)(response.bodyText);
					
				};
				
				this.$http.get(this.getURL).then(f, f);
			},
			show_code(e){
				return [e.code_system.trim(), e.code.trim(), e.designation.trim()].join(" | ");
			}
		}
		
	});


	this.reset_data_values = () => {
		self.data.tester_from_site = "";
		self.data.tester_from_code = "";
		self.data.tester_to_site = "";
		self.data.getResult = "";
		self.data.getURL = "";
	};

	
	this.update = function(){
		console.log("update");
		self.reset_data_values();
		
		Vue.http.get('/c3-cloud/all/')
			.then(response => {
				var o = JSON.parse(response.bodyText);
				console.log(o);
				// Object.keys(o).forEach(k => self.data[k] = o[k])
				self.data.sites = o.data.sites;
				self.data.concepts = o.data.concepts;
				self.data.code_systems = o.data.code_systems;
				
				
				var headers = Object.keys(o.data.mappings[0]);
				
				// following block is for vuetify format
				self.data.headers = $.map(
					headers,
					h => {return {text:h, value:h};}
				);

				self.data.mappings = $.map(
					o.data.mappings,
					m => {
						m.text="o"; // ???????
						m.value="i";
						return m;
					}
				);

			}, response => {
				console.log("error while updating data");
				console.log(response);
			});

		// Vue.http.get('/c3-cloud/concepts/')
		// 	.then(response => {
		// 		self.data.concepts = JSON.parse(response.bodyText).data
		// 	}, response => {
		// 		console.log("error while fetching concepts")
		// 		console.log(response)
		// 	});
		
	};

	// Routing
	const routes = [
		{ path: '/',
		  component: Vue.component('request-tester'),
		  alias: '/main'
		},
		{ path: '/about', component: Vue.component('about') },
		{ path: '/table', component: Vue.component('vue-table') },
		{ path: '/mapping-editor', component: Vue.component('mapping-editor') }
	];
	// Router options
	const router = new VueRouter({
		linkActiveClass: 'active',
		routes
	});
	
	router.afterEach((to, from) => {
		console.log("hash change: " + from.path + " -> " + to.path);
		self.update();
	});

	
	const app = new Vue({
		el: '#app',
		router
	});
	
	// debug
	window.data = data;

	this.update();

})(window,jQuery);
