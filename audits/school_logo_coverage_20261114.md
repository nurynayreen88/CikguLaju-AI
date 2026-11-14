# Audit penambahan logo sekolah rendah CikguLaju

14 November 2026, waktu Malaysia.

Katalog produksi sebelum penambahan meliputi 7,634 daripada 7,778 sekolah rendah. Import menambah 114 logo baharu, menjadikan liputan 7,748 daripada 7,778 sekolah (99.6%). Sebanyak 30 sekolah masih memerlukan sumber logo yang dapat disahkan.

Padanan dibuat melalui kod dalam direktori Supabase dan semakan visual lencana. Imej yang diluluskan ditukar kepada PNG, diuji dengan parser CikguLaju, dan dimuat naik ke katalog persendirian dengan `x-upsert: false`. Setiap fail dibaca semula melalui laluan storan yang digunakan oleh Web dan disahkan melalui SHA-256. Sebanyak 42 ujian Python dan dua ujian DOM lulus. Laluan pratonton Web produksi disahkan memerlukan sesi. Paparan melalui sesi guru produksi belum diuji.

Sumber utama ialah fail profil Pandai yang dinamakan dengan kod sekolah. Baki imej disemak melalui laman sekolah dan penerbitan sekolah. Beberapa logo daripada dokumen diambil dengan memotong kawasan lencana. Logo SK Kendaie dikreditkan kepada SK Kendaie di Wikimedia Commons (CC BY-SA 4.0) dan dikecilkan untuk katalog.

## Logo tambahan

| Kod | Sekolah | Sumber | SHA-256 |
| --- | --- | --- | --- |
| ABA2053 | SEKOLAH KEBANGSAAN PERPADUAN | [Pandai](https://app.pandai.org/uploads/school/ABA2053.jpg) | `45ec6417ef8e6272f10679db349886580a753c192e220c3130a898ec980034ea` |
| ABA4014 | SEKOLAH KEBANGSAAN SYEIKH MOHD. IDRIS AL-MARBAWI | [Halaman sumber](https://sites.google.com/moe-dl.edu.my/al-marbawi-digital/home) | `1e303f0ab93467ee6658b98b53bddea97df0bc3aa581e31c2622a03fdee1e067` |
| ABA5014 | SEKOLAH KEBANGSAAN SUNGAI RUSA | [Pandai](https://app.pandai.org/uploads/school/ABA5014.jpg) | `b0d095f7b36cd226b258fd62b72407ea73ab756a0eda7cdb342563341aa3a5a8` |
| ABA7037 | SEKOLAH KEBANGSAAN RPS BANUN | [Halaman sumber](https://skbanun.blogspot.com/) | `de6573eec7fc36440317d3d0b8dcb3c6cd5b52c5ba821790b9f83fb0331628e1` |
| ABA9006 | SEKOLAH KEBANGSAAN KUALA DIPANG | [Halaman sumber](https://skualadipang.blogspot.com/) | `82035897ae2d50216b4a67dab95d02639997bcf1844b4603e770dbb74b8ce40a` |
| ABAB002 | SEKOLAH KEBANGSAAN SERI BARU | [Halaman sumber](https://anyflip.com/iloky/alhk/basic) | `ec5f0c7d9eddef66a2e29d96a2c589a89fe5cdc49feb6449366488cbad2bca4f` |
| ABC2134 | SEKOLAH JENIS KEBANGSAAN (CINA) KAMPUNG BALI | [Pandai](https://app.pandai.org/uploads/school/ABC2134.jpg) | `7491e2a142ce4273d856fe3e3056a852ea0ea86a0f2efa3adc33afe4b1eaf1f4` |
| ABC2140 | SEKOLAH JENIS KEBANGSAAN (CINA) SUNGAI DURIAN | [Pandai](https://app.pandai.org/uploads/school/ABC2140.jpg) | `5c65240e24354c4d81921db8c0b01219e092fe859e45f346a692392d211e0ec8` |
| ABC7041 | SEKOLAH JENIS KEBANGSAAN (CINA) AYER KALA | [Pandai](https://app.pandai.org/uploads/school/ABC7041.JPG) | `c018423c8361b699b51385563c9da03cc0dc5459b51f44851ff3ec933ede66f0` |
| ABCB005 | SEKOLAH JENIS KEBANGSAAN (CINA) SIN MIN | [Halaman sumber](https://mysinmin.blogspot.com/2011/07/lencana-sekolah.html) | `a2980ab31db0f7f18a7307483470c01842d909f5f0add3af12c40034343c34c0` |
| ABD3057 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG SELINSING | [Pandai](https://app.pandai.org/uploads/school/ABD3057.JPG) | `e8261a8a269ed12aa27bc0d66d73ebf7a842eee234974de4404104ef6b6546fc` |
| ABD5102 | SEKOLAH JENIS KEBANGSAAN (TAMIL) THIRUVALLUVAR | [Pandai](https://app.pandai.org/uploads/school/ABD5102.JPG) | `2fb948dfdf0ec04931cb188bb01a7bfd5b7d524bd59cf0eda93bd310a32b6d92` |
| ABD5111 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG SUNGAI TIMAH | [Pandai](https://app.pandai.org/uploads/school/ABD5111.png) | `ab695c372660627505b4deeb6868721f440bc48109bff6552d0668b63023ffc1` |
| BBA3034 | SEKOLAH KEBANGSAAN SAUJANA UTAMA IJOK | [Pandai](https://app.pandai.org/uploads/school/BBA3034.JPG) | `77ecd96c288fafc6c64ba9e307fd46535ab38dcc327dca70be769e4a8aaadc63` |
| BBA6032 | SEKOLAH KEBANGSAAN BINJAI JAYA | [Pandai](https://app.pandai.org/uploads/school/BBA6032.jpg) | `dc679f31e9ad5f38461014bdfe4b7159090e19dd688a64e1d35641fc4e5a2df4` |
| BBA8210 | SEKOLAH KEBANGSAAN TAMAN DATO' HARUN (SATU) | [Pandai](https://app.pandai.org/uploads/school/BBA8210.jpg) | `cec66db14dc5f6824512285b47d6c4b09dd9712e493055a0976911be6f7325d8` |
| BBB0028 | SEKOLAH KEBANGSAAN CONVENT (2) | [Pandai](https://app.pandai.org/uploads/school/BBB0028.jpg) | `e74c27cfdef8a82be4d66f4127b90af90e34ee85f7e0ad3f11950fa7569bb62f` |
| BBB8301 | SEKOLAH KEBANGSAAN ASSUNTA SATU | [Halaman sumber](https://linktr.ee/skassuntasatu) | `c60d2327958ab0ee92514f1d3e25b305dd000347756f75044013cc2fe819aedc` |
| BBD3052 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LDG BKT IJOK | [Pandai](https://app.pandai.org/uploads/school/BBD3052.png) | `12bfd2064ba6bbd501362203bab5ef9438943da46c0cba5d39387a8d5a69d42b` |
| BBD5052 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG MINYAK | [Pandai](https://app.pandai.org/uploads/school/BBD5052.jpg) | `3a75cffb3fd5785729e5feef56ef316d1ff2afdcd115340a7b66c1c561b78f47` |
| BBD8461 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG EBOR | [Pandai](https://app.pandai.org/uploads/school/BBD8461.png) | `4d845127c5524ea85aac0f79dcc5c4d30e107c440fc10d41a738a1603a377c1b` |
| CBA3059 | SEKOLAH KEBANGSAAN RPS BETAU (JHEOA) | [Pandai](https://app.pandai.org/uploads/school/CBA3059.jpg) | `47668145d67a623900e38fb836970c72e74a86747f6fce078438c33a02bac5ae` |
| CBA4114 | SEKOLAH KEBANGSAAN CHENGAL LEMPONG | [Halaman sumber](https://anyflip.com/lkxol/quxp/basic) | `1ff0add266d44dd97b738fbec868c6b84c8b3f5550bb2e2f3eeefcde02285c11` |
| CBA6026 | SEKOLAH KEBANGSAAN SATAK | [Pandai](https://app.pandai.org/uploads/school/CBA6026.jpg) | `015c0927b4c964c6331e6a1243e577d5fdf19455492220fc8a706f252fd09c42` |
| CBC6040 | SEKOLAH JENIS KEBANGSAAN (CINA) SG KLAU | [Pandai](https://app.pandai.org/uploads/school/CBC6040.JPG) | `8f901ab11d4f1e1f4101de12a5e1d9ce953a0253b781d4eb2e14a6daff758dd2` |
| DBA0014 | SEKOLAH KEBANGSAAN KANDIS | [Pandai](https://app.pandai.org/uploads/school/DBA0014.png) | `b115170846837e75450acdc1df7428aaa205d38e2b18e1a3bee047be9fb310c2` |
| DBA1048 | SEKOLAH KEBANGSAAN CHE DERIS | [Pandai](https://app.pandai.org/uploads/school/DBA1048.jpg) | `d29bd281a6beda179c01cc67716cc59f3c06e77c1171e12a77e13c5652069cda` |
| DBA1068 | SEKOLAH KEBANGSAAN KOTA | [Pandai](https://app.pandai.org/uploads/school/DBA1068.jpg) | `9f7b095d5058db53099cd595daa53c5136d548eb083269dc8b9c1a94a33edb0c` |
| DBA1071 | SEKOLAH KEBANGSAAN MELOR | [Pandai](https://app.pandai.org/uploads/school/DBA1071.jpg) | `384647d5810c98ab7ec7083b45aec3ce0c6980b5c6bf743b2e8e709672cb67c9` |
| DBA1093 | SEKOLAH KEBANGSAAN PULAU GAJAH | [Pandai](https://app.pandai.org/uploads/school/DBA1093.JPG) | `fd65917828e2be5d778aeac10a6f2b0dbac66a9aed61b92acb223d4567abe70f` |
| DBA1102 | SEKOLAH KEBANGSAAN TAPANG | [Pandai](https://app.pandai.org/uploads/school/DBA1102.jpg) | `5ab815dda543e4de9daf392f872f1b0241c3f1b4113e62af99358826ebf4b9fe` |
| DBA2183 | SEKOLAH KEBANGSAAN PANGKAL GONG | [Pandai](https://app.pandai.org/uploads/school/DBA2183.jpg) | `4cbffb9766671f342f2aba38b41bd37d7f27c913d7ada0c3b20f3bafc81e392b` |
| DBA3212 | SEKOLAH KEBANGSAAN KEDONDONG | [Halaman sumber](https://anyflip.com/kuwpo/kwvd/basic) | `593390b6780006c2e346ffd16572258309dec2a7b953d2e22fc88c447a7d0ba1` |
| DBA3220 | SEKOLAH KEBANGSAAN LEMAL | [Pandai](https://app.pandai.org/uploads/school/DBA3220.png) | `668e8fc349bc0660cd471f9c1cc6df8d5fc766c27ea511ef2597eb7ac2164cd8` |
| DBA3231 | SEKOLAH KEBANGSAAN SRI KIAMBANG | [Pandai](https://app.pandai.org/uploads/school/DBA3231.jpg) | `99a58f8bec10bdc4781931b246d5ca9e9180a90f010af59d1c558afe208cfcb8` |
| DBA6346 | SEKOLAH KEBANGSAAN PULAU BELURU | [Pandai](https://app.pandai.org/uploads/school/DBA6346.JPG) | `e5f9efc462afaf1cb8036a8f19882e8c0b048813e21e12fd9ed2f62f2ec1d2ce` |
| DBA7376 | SEKOLAH KEBANGSAAN KAMPONG KARANGAN | [Pandai](https://app.pandai.org/uploads/school/DBA7376.JPG) | `4940eb451cd294c71155f7ca7b3f668dee25fa1abeaf5a3db449f12353dc8c65` |
| DBB6355 | SEKOLAH KEBANGSAAN SERI WAKAF BAHARU | [Pandai](https://app.pandai.org/uploads/school/DBB6355.png) | `490ed15438a09d61035cb8df6c4495b51647173c42b92831a1883b3e73fa4191` |
| JBA1045 | SEKOLAH KEBANGSAAN TIRAM DUKU | [Pandai](https://app.pandai.org/uploads/school/JBA1045.jpg) | `81597d164b27df66d7e4d0f9b80fc4bf65e02241f2df650aaa63a61515f00f51` |
| JBA3001 | SEKOLAH KEBANGSAAN BANDAR | [Halaman sumber](https://sites.google.com/moe-dl.edu.my/lamansebaktidigitalhub/home) | `44f7a67fa80bdc4b5a39c10256a019e1e2ab9d5f07d61436e4c9107cbcf1a15f` |
| JBA3016 | SEKOLAH KEBANGSAAN PENGERANG | [Pandai](https://app.pandai.org/uploads/school/JBA3016.jpg) | `e972fc75eacd181b41d9429d7a11d3674a6b8ea2fca54ad79fdae3a1737c5f7a` |
| JBA3040 | SEKOLAH KEBANGSAAN LKTP SUNGAI MAS | [Pandai](https://app.pandai.org/uploads/school/JBA3040.png) | `79899e674802cd1a72a47dde521effa7653877e537def241f74c2f7577287859` |
| JBA5071 | SEKOLAH KEBANGSAAN PARIT NO. 5 | [Halaman sumber](https://skpn5muar.blogspot.com/2017/11/profil-sk-parit-no-5.html) | `f871fd0161caaccf2a250af37a7b2149e46c58ac818a085a30cbe54e572cf006` |
| JBA9018 | SEKOLAH KEBANGSAAN LEDANG | [Halaman sumber](https://anyflip.com/homepage/hfjhv) | `ab7fd100509a72621ce884e341b39eef1aa0f73106fcc8ce66a814db22792e25` |
| JBC0004 | SEKOLAH JENIS KEBANGSAAN (CINA) CHENG SIU 1 | [Pandai](https://app.pandai.org/uploads/school/JBC0004.JPG) | `577b53b1dfd3aee96210afd1556601f2573b443df1095d592a9b47481e3f41f2` |
| JBC5023 | SEKOLAH JENIS KEBANGSAAN (CINA) CHUNG SUN | [Pandai](https://app.pandai.org/uploads/school/JBC5023.jpg) | `bf9d1c55eb50ceeb9dcb9fd9658e180a91abcb2212341950e26f4c9fb733e55e` |
| JBC9016 | SEKOLAH JENIS KEBANGSAAN (CINA) PUI NAN | [Halaman sumber](https://30.com.my/sjkc/pui-nan-johor/) | `fb821df53bf24c4fe46b27bc997f524f30255b108c3027c290e67938e4208cd3` |
| JBD0050 | SEKOLAH JENIS KEBANGSAAN (TAMIL) SRI GADING | [Pandai](https://app.pandai.org/uploads/school/JBD0050.jpg) | `0f2588a49092880367719c156769d082f5b027a3d217463d2ffc03402b6ab873` |
| KBA0020 | SEKOLAH KEBANGSAAN KUALA SAMAK | [Pandai](https://app.pandai.org/uploads/school/KBA0020.JPG) | `764e562b89c042632dba63d8daeac4eaa13110546042ed9ddd347115b224af25` |
| KBA0024 | SEKOLAH KEBANGSAAN TANJUNG PARI | [Pandai](https://app.pandai.org/uploads/school/KBA0024.jpg) | `430de18a36e7c677978ae331bb83de543fb28bd41c494537b81e0cd9ea3718a0` |
| KBA5005 | SEKOLAH KEBANGSAAN JUNJONG | [Pandai](https://app.pandai.org/uploads/school/KBA5005.JPG) | `069b54516f5a4f2f47bcc4e9b0e190e6046115da7ce7b524b7366ec4e1944869` |
| KBA5017 | SEKOLAH KEBANGSAAN SUNGAI SELUANG | [Pandai](https://app.pandai.org/uploads/school/KBA5017.jpg) | `58989beff8e9ab6ab5b1b37ad54bea38b3748c6bbe21a7a84f182c539bf48b1c` |
| KBA8009 | SEKOLAH KEBANGSAAN SERI AMPANG MUDA | [Pandai](https://app.pandai.org/uploads/school/KBA8009.JPG) | `8e5cb9dd01b81e46eec1f87aea617503d6d522e0875a36f924973e04345391fb` |
| KBA8017 | SEKOLAH KEBANGSAAN DANGLAU | [Pandai](https://app.pandai.org/uploads/school/KBA8017.jpg) | `e91ac4b67366496177b4432c201028f99b22d64a241b27e2ebb32b7a471f07be` |
| KBA8018 | SEKOLAH KEBANGSAAN SIK DALAM | [Halaman sumber](https://anyflip.com/iihla/ddtg/basic/) | `87960113d50572ac8f2d5ae2676cb9f3ee1def26ecf6d38daa99d429e30f2ad4` |
| KBAB015 | SEKOLAH KEBANGSAAN BUKIT PAK KIAU | [Pandai](https://app.pandai.org/uploads/school/KBAB015.jpg) | `6194ee824f5200a9845c63581d2b9f3536d0b6fa92293e69ff3fed8b6bd5fed2` |
| KBC4046 | SEKOLAH JENIS KEBANGSAAN (CINA) LAM MIN | [Pandai](https://app.pandai.org/uploads/school/KBC4046.png) | `11a314e6921062dcf17070339f571745a28db10fcc5309bfeb5a2cf8ee948313` |
| KBC9027 | SEKOLAH JENIS KEBANGSAAN (CINA) PEI ENG | [Pandai](https://app.pandai.org/uploads/school/KBC9027.jpg) | `a9ee646962a2bf11a28113c3043332a667700e07090cc2f5ec85271c22c7bc21` |
| MCT0002 | SEKOLAH RENDAH ARAB JAIM AL-FAIZIN | [Pandai](https://app.pandai.org/uploads/school/MCT0002.JPG) | `fc822b6c6af735abcc5d0af40e1f6a23501d313abe0718e9f29e20ccf93a6930` |
| NBA0011 | SEKOLAH KEBANGSAAN DATUK UNDANG ABDULLAH | [Halaman sumber](https://seeklogo.com/vector-logo/615875/sekolah-kebangsaan-datuk-undang-abdullah) | `d95cd9a6914bb59069a4a2f8b133890fd9c1fd544b308d018b5f8b1fee952065` |
| NBA1006 | SEKOLAH KEBANGSAAN KAMPONG PARIT | [Pandai](https://app.pandai.org/uploads/school/NBA1006.JPG) | `3281e2e593c6e653a1cfbe9c78ed0735cdbe247aee79eaed888dee452d744237` |
| NBA1032 | SEKOLAH KEBANGSAAN TENGKEK | [Pandai](https://app.pandai.org/uploads/school/NBA1032.JPG) | `ca6667fe1f769614b580e8f9a55be3966d98b1e0cdda81a13cc7ab04406ffe79` |
| NBA1111 | SEKOLAH KEBANGSAAN BUKIT ROKAN BARAT | [Pandai](https://app.pandai.org/uploads/school/NBA1111.jpg) | `4ddb81d16d5f0e857dd95ec9dd89fb06bbd0ee39e835354de808eccbdbbaa859` |
| NBC5024 | SEKOLAH JENIS KEBANGSAAN (CINA) SIN MIN GEMENCHEH | [Pandai](https://app.pandai.org/uploads/school/NBC5024.jpg) | `5b83c517678c70c1dc886a71cce23acd6a4fabe627a844a2b153add51060531c` |
| NBC5027 | SEKOLAH JENIS KEBANGSAAN (CINA) LADANG REGENT | [Pandai](https://app.pandai.org/uploads/school/NBC5027.jpg) | `348cd0c12da51a456d2ff0677a7eed8b37c00b79288e10b932e4117cb2f4752a` |
| NBD2042 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG TANAH MERAH | [Halaman sumber](https://anyflip.com/wargc/ozgv/basic) | `fe615e0c7f2f8b20c939ad99d36dbf52f2df12c9241a841e6e8da84b31f8b7dd` |
| NBD6011 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LDG MIDDLETON | [Halaman sumber](https://sjktladangmiddleton.blogspot.com/) | `58606a80903cfcb5a8d4ff27431555d813f78157e9181830c91aae13e7c55294` |
| PBA0011 | SEKOLAH KEBANGSAAN MENGKUANG | [Halaman sumber](https://sistemguruonline.my/wp-content/uploads/2022/10/SS-MENGKUANG.pdf) | `f6cb6156194ec70b036388531e963bb51814edb0b70bd833aaea3ef90b3805b4` |
| PBB1017 | SEKOLAH KEBANGSAAN CONVENT LEBUH LIGHT | [Pandai](https://app.pandai.org/uploads/school/PBB1017.jpeg) | `77e2685cf2e977c7a2543c55187ac16f68db456071a764c9bd7116fce817f73d` |
| PBC2043 | SEKOLAH JENIS KEBANGSAAN (CINA) LEE CHEE | [Pandai](https://app.pandai.org/uploads/school/PBC2043.jpg) | `480a661e274b72ad077ae145e0639b91279e08af28e853a4b8f4104ac383e511` |
| RBA0034 | SEKOLAH KEBANGSAAN TAMBUN TULANG | [Pandai](https://app.pandai.org/uploads/school/RBA0034.JPG) | `fc335892d6847192aa3f2c737217c0374612932debb8ca6070670cbcb416e1ed` |
| TBA0013 | SEKOLAH KEBANGSAAN GONG BAYOR | [Pandai](https://app.pandai.org/uploads/school/TBA0013.jpg) | `e42de965116d3319a77ad35c502f3b37b1c4a78af9599d7593fffcfe17be2a1f` |
| TBA0080 | SEKOLAH KEBANGSAAN NYIUR TUJUH | [Pandai](https://app.pandai.org/uploads/school/TBA0080.JPG) | `cfa4d225df0ceb220756e377d5859acd956f989ff69ed1d46ac03fa576cd3187` |
| TBA3029 | SEKOLAH KEBANGSAAN BANGGOL KATONG | [Pandai](https://app.pandai.org/uploads/school/TBA3029.PNG) | `ddbf6167cc6e85403aaa786c3e55a2b123e024d2098f8f08cc2bdf76d80adc43` |
| TBA6092 | SEKOLAH KEBANGSAAN SERI KASAR | [Halaman sumber](https://anyflip.com/jmofp/aowf/basic) | `64ad7fb48f9517619d10cee3c210468d9e0a23f2ba43a73e9d9c0db5d4f0fb1c` |
| WBA0005 | SEKOLAH KEBANGSAAN TUN HUSSEIN ONN | [Pandai](https://app.pandai.org/uploads/school/WBA0005.JPG) | `a2adf1135b39bfd3f0e6e300bb18f2861377048adc0303f85041f321f39bbe31` |
| WBA0009 | SEKOLAH KEBANGSAAN SENTUL 1 | [Pandai](https://app.pandai.org/uploads/school/WBA0009.png) | `0be2956e26f10f506c7b70de6b3816b595af41029c1c800af45c2b9092385fb7` |
| WBA0018 | SEKOLAH KEBANGSAAN TAMAN TUN DR ISMAIL 1 | [Halaman sumber](https://sites.google.com/moe-dl.edu.my/sktamantundrismail1/pengenalan/logo-sekolah) | `b243c82d6b8611e5a33ab54fcf0ef0e278efaef90ed75b48caa29305022b715c` |
| WBB0054 | SEKOLAH KEBANGSAAN CONVENT SENTUL 2 | [Pandai](https://app.pandai.org/uploads/school/WBB0054.jpg) | `fe8b51743ae88183138005405d311babce20f3fabe80666a3e47e2dec6e16a87` |
| WBB0060 | SEKOLAH KEBANGSAAN (P) METHODIST (1) BRICKFIELDS | [Pandai](https://app.pandai.org/uploads/school/WBB0060.jpg) | `982d38ef4136a30aa5dc6d45b0a087071b3243d6c40c879829e2625f3ce557e2` |
| WBB0072 | SEKOLAH KEBANGSAAN (L) METHODIST SENTUL | [Pandai](https://app.pandai.org/uploads/school/WBB0072.jpg) | `03cbdc999e336d2c54044efe3e68deec2ba82209ca76ae4d7fe597c57245a2ff` |
| WBB0097 | SEKOLAH KEBANGSAAN (1) BATU 4 JALAN IPOH | [Pandai](https://app.pandai.org/uploads/school/WBB0097.jpg) | `a9830e6938982a2447d4487d93d0afa294e2359f385f0d457ba77f807ad86642` |
| XBA1040 | SEKOLAH KEBANGSAAN SODOMON | [Pandai](https://app.pandai.org/uploads/school/XBA1040.png) | `eba3736dc57d65a97d16b0122a84cfaa27f7f4f764d7850d88bd37e85f2ae671` |
| XBA1110 | SEKOLAH KEBANGSAAN KG BAHAGIA | [Pandai](https://app.pandai.org/uploads/school/XBA1110.jpg) | `af3e0f878d3d44c6ff193ea4534f21e3bdabc91eba054002c8e3efa54df579ec` |
| XBA2003 | SEKOLAH KEBANGSAAN BONGON BESAR | [Pandai](https://app.pandai.org/uploads/school/XBA2003.png) | `1f573ddb3e78a1073e7c3b65048e3e908a0e4029edc83c9d0ffdd60396df2f9d` |
| XBA2013 | SEKOLAH KEBANGSAAN SAKILAN DESA | [Halaman sumber](https://sites.google.com/moe.gov.my/ptis-sandakan/kumpulan-1/sk-sakilan-desa) | `2b358d3a8340b52bd60ab95e2b75c8f9d94b95d3c7a1e4447377e7e6ad2f0713` |
| XBA4308 | SEKOLAH KEBANGSAAN BUNGALIO | [Pandai](https://app.pandai.org/uploads/school/XBA4308.jpg) | `29a84ddf5965db9194d25598114e846171b15441b55dea215d70811c81b25f2b` |
| XBA4411 | SEKOLAH KEBANGSAAN LINUNGKUAN | [Pandai](https://app.pandai.org/uploads/school/XBA4411.png) | `425177ba0c5ed44b0affb9b839bcd6d732756a8322b7e4452ae2ffcee6e41f6a` |
| XBA4413 | SEKOLAH KEBANGSAAN RUNGUS | [Pandai](https://app.pandai.org/uploads/school/XBA4413.png) | `53e6994ca8a431d9aba72397e21877408df6b39add6668d085cd6896a5d48abe` |
| XBA5003 | SEKOLAH KEBANGSAAN LAKSIAN | [Pandai](https://app.pandai.org/uploads/school/XBA5003.png) | `ccc725f63b5db9418212e1c6cee580c1d13b3e15ffc562b0ee67e23c5343366e` |
| XBA5076 | SEKOLAH KEBANGSAAN TIGA PAPAN KUDAT | [Pandai](https://app.pandai.org/uploads/school/XBA5076.jpg) | `dadf9dbd4f26fc1ebfd259c6a0e0022f3b494d1fd16c866dc383eff5750b0758` |
| XBA5403 | SEKOLAH KEBANGSAAN BUNDU TUHAN | [Pandai](https://app.pandai.org/uploads/school/XBA5403.JPG) | `862de7660100c91ef384ac1473774af864784f30aafb50f894b3837f37b70113` |
| XBA5409 | SEKOLAH KEBANGSAAN KIMONDOU | [Pandai](https://app.pandai.org/uploads/school/XBA5409.JPG) | `60cb73a2aa126f1186d54e9496aa9cde904fe6afc37f70ae503d425e015575d1` |
| XBA5419 | SEKOLAH KEBANGSAAN MARAKAU | [Pandai](https://app.pandai.org/uploads/school/XBA5419.png) | `fd1f38b88141897b9e5c64db98c47548c131d8d2da89c21dd42f4cad3861168e` |
| XBA5438 | SEKOLAH KEBANGSAAN RATAU | [Pandai](https://app.pandai.org/uploads/school/XBA5438.jpg) | `1210fa96e53183c4011e6e2ff54e424fcb22ad0ca5366944b46a2e65e545e781` |
| XBA5445 | SEKOLAH KEBANGSAAN TINANOM | [Pandai](https://app.pandai.org/uploads/school/XBA5445.JPG) | `5f5de32c02e3796011b8337602378ae98a026c9f1e0e9b2adffa42b431d4e382` |
| XCA5078 | SEKOLAH KEBANGSAAN TINANGOL | [Pandai](https://app.pandai.org/uploads/school/XCA5078.jpg) | `867b37b02af47afcd298289371c96506a1efbc2a19610bfd7158db4e718e9dba` |
| YBA5120 | SEKOLAH KEBANGSAAN TANJONG | [Pandai](https://app.pandai.org/uploads/school/YBA5120.jpg) | `c542db837c46c657e76c87587b38dab406085a4b51e95562e2aa0f5efd672b88` |
| YBA8116 | SEKOLAH KEBANGSAAN NIUP | [Pandai](https://app.pandai.org/uploads/school/YBA8116.jpg) | `f21559f4e38dd6403d08b69d7b2fe75e487277b88abd035b4cc4fa2b418e8738` |
| YBB1410 | SEKOLAH KEBANGSAAN BIAWAK | [Pandai](https://app.pandai.org/uploads/school/YBB1410.jpg) | `d646c2438166155fa2a44b59fc52d70d7c520e985c00afdbe978fa216259dfe4` |
| YBB1418 | SEKOLAH KEBANGSAAN KENDAIE | [Halaman sumber](https://commons.wikimedia.org/wiki/File:LOGO_SK_KENDAIE.png) | `938cc7c779b7c21584a05712ca98acf5f8345271d9f744766e396209c1e14749` |
| YBB2112 | SEKOLAH KEBANGSAAN SELANJAN | [Halaman sumber](https://sites.google.com/moe.edu.my/i-skasskselanjan/home) | `0275c95ecf997c160833736064401e62b5b8db88933b87a8c9c9eaa526315bd8` |
| YBB2139 | SEKOLAH KEBANGSAAN SEMBAYANG | [Pandai](https://app.pandai.org/uploads/school/YBB2139.JPG) | `6d751939c85ce412e39afef75856cc0e1020c625ccae09d8d2741d39480bb948` |
| YBB3207 | SEKOLAH KEBANGSAAN TANJUNG PENASU | [Pandai](https://app.pandai.org/uploads/school/YBB3207.jpg) | `de59fb3b1c0bd90d49229d620566dd5a0397c74fe8bc5ab387cf53d832a88164` |
| YBB4313 | SEKOLAH KEBANGSAAN LONG BEDIAN | [Pandai](https://app.pandai.org/uploads/school/YBB4313.jpg) | `e843801d1b9b060f1e9e45e97e896f2a49c4a852336fbce68302903640ca6e72` |
| YBE4104 | SEKOLAH KEBANGSAAN SAYED OTHMAN | [Pandai](https://app.pandai.org/uploads/school/YBE4104.jpg) | `61c8fc144cfcaed468afabb411941d9a44f3ac211e10dde01dcbcec83f443098` |
| YCB1334 | SEKOLAH KEBANGSAAN ST SWITHUN | [Pandai](https://app.pandai.org/uploads/school/YCB1334.jpg) | `1573f63f4b64ad9d078e15ccb78cb3b76ae2155bf36014d054ec7d2d43d803bb` |
| YCB8202 | SEKOLAH KEBANGSAAN ST PHILIP BUGU | [Pandai](https://app.pandai.org/uploads/school/YCB8202.jpg) | `4daf33f75965839ceb95e597bbce77bf4de3ec859a8d4bb94d1b1c4e5ed08d3f` |
| YCC1302 | SEKOLAH JENIS KEBANGSAAN (CINA) CHUNG HUA SG TENGAH | [Pandai](https://app.pandai.org/uploads/school/YCC1302.JPG) | `bbb62b92d3b69d2dba95feafb2f7c2db28244a6345370510d0f3fc5e25165a9b` |
| YCC3223 | SEKOLAH JENIS KEBANGSAAN (CINA) ING GUONG | [Pandai](https://app.pandai.org/uploads/school/YCC3223.jpg) | `87584271bcd6446c897d9fef14350e6ae86ae60ddab89d9326440c28d1f209e1` |
| YCC3233 | SEKOLAH JENIS KEBANGSAAN (CINA) HING UNG | [Pandai](https://app.pandai.org/uploads/school/YCC3233.jpg) | `c3b7c481dd31b604a153aa4d6ee830cef5e6b4e37c7a241de22de583086d8062` |
| YCC4102 | SEKOLAH JENIS KEBANGSAAN (CINA) CHUNG HUA KROKOP | [Pandai](https://app.pandai.org/uploads/school/YCC4102.jpg) | `29fba931c15ba8a9da8d3328d17567900b651cb8e7d4aa06711fa9dfcfec683d` |
| YCC6107 | SEKOLAH JENIS KEBANGSAAN (CINA) SU TAK | [Pandai](https://app.pandai.org/uploads/school/YCC6107.jpg) | `a1b130e6e746e8f5f269fd8f977e9deec6e0dfc958c7d8e5665959961a9e08b3` |
| YCC6304 | SEKOLAH JENIS KEBANGSAAN (CINA) YONG KWONG | [Pandai](https://app.pandai.org/uploads/school/YCC6304.jpg) | `dfaa1496d4dcf56aaf83207c3b9b9e2ba71b3f6278f38a8e195bf84e23e6c2fd` |

## Kemas kini katalog produksi, 14 November 2026

Pusingan kedua menambah 20 logo. Semakan terus terhadap storan produksi mengesahkan 7,768 daripada 7,778 sekolah rendah mempunyai imej katalog (99.87%). Setiap imej baharu dibaca semula dari laluan storan persendirian dan SHA-256 sepadan. Sebahagian imej ialah potongan lencana beresolusi rendah daripada bahan sekolah atau foto papan tanda.

| Kod | Sekolah | Sumber | SHA-256 |
| --- | --- | --- | --- |
| ABA7036 | SEKOLAH KEBANGSAAN RPS POS KEMAR | [Blog SK RPS Kemar, foto papan tanda](https://skrpskemar.blogspot.com/) | `6386121afa79e74393b6305f833d39deedd2b1fed391db41bfdaceb2b777d693` |
| ABAB025 | SEKOLAH KEBANGSAAN SUNGAI TIANG BAROH | [Buku Mesyuarat Agung PIBG SK Sungai Tiang Baroh](<https://anyflip.com/haskq/iqbp/basic>) | `b762e61cdd3776e6d86c5e5048027820e20440c1509980b5921a458859534523` |
| ABC1056 | SEKOLAH JENIS KEBANGSAAN (CINA) CHIEN HUA | [Blog SJKC Chien Hua, foto papan tanda](<https://sjkchienhua.blogspot.com/2015/03/blog-post.html>) | `3e35922070ad8c177f4e8d18b00a0d311bc279c4943e6a59b9bdc0a7c65ec8a0` |
| ABCA001 | SEKOLAH JENIS KEBANGSAAN (CINA) HO PIN | [The Community Chest, foto papan tanda](<https://commchest.org.my/projects/sjkc-ho-pin/>) | `a31eea31f944434a0e950b33eef14136e68d50fec456e77bbcd13c966440a0e2` |
| ABCB003 | SEKOLAH JENIS KEBANGSAAN (CINA) POOI AING | [Laporan SJKC Pooi Aing](<https://anyflip.com/lusri/gihq/basic>) | `c17719a2e8e5e243fe8afc779d1309245836b94a6225cc6c31a06a3fe6ba9871` |
| ABCB009 | SEKOLAH JENIS KEBANGSAAN (CINA) YEE HWA | [Blog SJKC Yee Hwa, lencana pada seragam](<https://sjkcyeehwasb.blogspot.com/>) | `78f15cf3a5614001ce12f013b70201efd59d15d915af3189e0c3ad2e9fdf04b8` |
| ABD1082 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG AYER TAWAR | [Blog SJKT Ladang Ayer Tawar](<https://sjktlat.blogspot.com/>) | `d0a2bb36168a5bdc0674ef21518c5d2a83866cffa329c5db7358a36855c87e49` |
| CBC6034 | SEKOLAH JENIS KEBANGSAAN (CINA) YUH HWA | [Majalah SJKC Yuh Hwa Bukit Koman 2024/2025](<https://online.anyflip.com/oomez/zluv/mobile/index.html>) | `d39cf8455db61278a25d71c8f9ade6b2ee448b8b816513da683d29f03f64b261` |
| DBA3237 | SEKOLAH KEBANGSAAN OTHMAN TALIB (2) | [Buku Program SK Othman Talib (2)](<https://anyflip.com/ztzjzr/mhtt/basic>) | `7e524a05f4aaf030f20b66692a6ad36073f4ffbb293fcf843d1e082c04483881` |
| JBC0035 | SEKOLAH JENIS KEBANGSAAN (CINA) YONG PENG 1 | [Buku Kejohanan Olahraga SJKC Yong Peng 1](<https://online.fliphtml5.com/ymrps/dyjm/files/shot.jpg?1>) | `24c52bca47f94e3dafa95fed75163d629af52b55426e1f5d348f657925b0fa06` |
| JBC9020 | SEKOLAH JENIS KEBANGSAAN (CINA) KEBUN BAHRU | [Foto Wee Hong di Wikimedia Commons, potongan dan penukaran PNG, CC BY-SA 4.0](<https://commons.wikimedia.org/wiki/File:SJK_(C)_Kebun_Bahru.jpg>) | `c09bb0f82902d361cc709f591d8323e5caf80e4de1769ecc6226e8f4def5cde6` |
| MBD0064 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG GADEK | [Kertas Kerja Bahasa Tamil SJKT Ladang Gadek](<https://www.scribd.com/document/989519902/Kertas-Kerja-B-tamil-2024>) | `34ac425004c6ff6245b942fafbd857ca52c2588a3c3d2f360d3c46ec15419a78` |
| PBC1046 | SEKOLAH JENIS KEBANGSAAN (CINA) AIK HUA | [Persatuan Hainan Pulau Pinang, poster SJKC Aik Hua](<https://www.hainan.my/aik-hua-school/>) | `b873792d18c0f915735b551f304f8ffc4b6bdd177e2fa39ef8c76571623aaa17` |
| XBA5203 | SEKOLAH KEBANGSAAN KANIBONGAN | [Blog SK Kanibongan Pitas](<https://sk-kanibongan.blogspot.com/p/panitia.html>) | `f345744266a4307ac73bbf8516ac5fd632ea8cfd637d674c13784c5c7e7f35b5` |
| XCC3041 | SEKOLAH JENIS KEBANGSAAN (CINA) SIN HWA | [Buku ulang tahun SJKC Sin Hwa Tawau](<https://anyflip.com/ibdxf/spwp/basic/101-150>) | `c6cd132c23205072d0483a34dcbcc71f0c696235323cde7bfb4b697475bf3c3c` |
| XCC5034 | SEKOLAH JENIS KEBANGSAAN (CINA) LOK YUK BATU 1 KUDAT | [Foto sekolah SJKC Lok Yuk Batu 1 Kudat](<https://30.com.my/wp-content/uploads/2022/08/SJKC-Lok-Yuk-Batu-1-Kudat-Kudat-Sabah-1.jpg>) | `01c21114d31ce487393eabd6d9102bfc852d252e88f898ccff8486c50a164f0b` |
| YBB3406 | SEKOLAH KEBANGSAAN SG ARAU | [Blog SK Sungai Arau Selangau](<https://sksungaiarauselangau.blogspot.com/2015/04/>) | `3062f0095f4e10ba8ecdcee0c70a14ff25c66d62acca0cddb4e512a585ae53f4` |
| YCB2102 | SEKOLAH KEBANGSAAN ST LAWRENCE | [Buku program PIBKS SK St Lawrence (M)](<https://fliphtml5.com/gglvm/zrpx/Dinner_PIBKS%272024/>) | `bdb4111349f216c8cc5a87d83a5767198537d8a083127677564dd54b0ffe6c22` |
| YCB8204 | SEKOLAH KEBANGSAAN ST MICHAEL MONGKOS | [Profil sekolah SK St Michael Mongkos](<https://www.schoolandcollegelistings.com/MY/Serian/117083944726083/SK-St-Michael-Mongkos-Serian>) | `f2d222a3b31ca5654c0cb2283bc0d42b74b46c300571eff157518f9d53cce241` |
| YCC3214 | SEKOLAH JENIS KEBANGSAAN (CINA) KAI NANG | [Profil sekolah SJKC Kai Nang](<https://www.schoolandcollegelistings.com/MY/Kuching/268362826366439/SJKC-KAI-NANG>) | `1c287873ebbe7057de282ad585867553247c833a5cd1d72816022544bd31c4c4` |

## Semakan susulan katalog produksi

Empat imej ditambah dan disahkan semula melalui SHA-256. Liputan kini 7,772 daripada 7,778 sekolah rendah (99.92%). Kod lama ABD5137 pada kepala surat SJKT Ladang Strathmashie dipadankan dengan kod semasa ABDB011 melalui [senarai sekolah Perak](https://myschoolchildren.com/data/SEK_REN_Perak_files/sheet001.htm).

| Kod | Sekolah | Sumber | SHA-256 |
| --- | --- | --- | --- |
| ABA0128 | SEKOLAH KEBANGSAAN JERNANG | [Minit HEM SK Jernang 2024/2025 dengan kod ABA0128](<https://www.scribd.com/document/753320071/Min-Mesy-HEM-Bil-1-2024-2025>) | `76d5480549b20c696d144dce9351b10ed10bc2704fbf8936ecacc884f1ea320c` |
| ABDB011 | SEKOLAH JENIS KEBANGSAAN (TAMIL) LADANG STRATHMASHIE | [Kepala surat sekolah dengan kod lama ABD5137](<https://id.scribd.com/doc/227336183/Contoh-Surat-Iringan-PPD>) | `fe283150e7d659ba4df38194d556945bc85f26baf377b6144c5aeba2f078197e` |
| YBB6314 | SEKOLAH KEBANGSAAN ULU MERADONG | [Buku Pengurusan SK Ulu Meradong dengan kod YBB6314](<https://www.scribd.com/doc/230899078/Buku-Pengurusan-Sekolah-2014-pptx>) | `8435d9f8b32587c6e567a713453a8f0a0f3df56dfa86ba0a70960ed9a0fa442d` |
| YCB1319 | SEKOLAH KEBANGSAAN GEORGE | [Buku program SK St George Punau](https://anyflip.com/xzkmv/hfjc/basic), [kod YCB1319 dalam direktori sekolah misi](https://www.fcmsm.org/wp-content/uploads/2024/03/Directory-2024-updated-March.pdf?x38165=) | `a39d560c053751936b4687c69882a7188174e2f93070dedfb55c714911813c4c` |

## Tiga lagi logo disahkan dalam produksi

Semakan storan produksi menunjukkan 7,775 daripada 7,778 sekolah rendah mempunyai logo katalog (99.96%). Ketiga-tiga imej baharu dibaca semula daripada storan dan disahkan dengan SHA-256.

| Kod direktori | Sekolah | Sumber | SHA-256 |
| --- | --- | --- | --- |
| KBC0047 | SJKC Poi Chee | [Logo oleh rakan projek landskap sekolah](https://maylandscape-interiors.com/wp-content/uploads/2025/08/poi-chee-logo.jpg) | `f2f9f1007c8dc420f83638ed7572280afcd8c7ce318e3da8a2f44a2c242d5a26` |
| XBA4376 | SK Wasai | [Kepala surat SK Wasai dengan kod XBA4376](<https://pt.scribd.com/doc/228775691/Surat-Iringan-Pengesahan-Lantikan-Audit-Dalaman>) | `f03d2cac8b033447046f1f2b50954ea37243b905b7440f968303e95083f4d3ab` |
| YCC1329 | SJKC Chung Hua Syn-San-Tu | [Buku profil KBAT sekolah, lencana bertulis Syn San Too](https://anyflip.com/aicza/dffm/basic) | `0aaec386c6cb1bc6939df657b0891291288d64979e5086f15afd22405b85ed9c` |

Poi Chee berpindah dari Malau, Baling, ke Sungai Petani dan menggunakan kod KBC3106 dalam direktori Dong Lian Kedah. Katalog Web masih mempunyai rekod KBC0047, jadi logo dipadankan pada kod tersebut. [Laporan perpindahan](https://www.orientaldaily.com.my/news/north/2024/03/10/636512) · [Direktori Dong Lian Kedah](https://dongliankedah.com/吉打州国民型华文小学/)

## Sekolah yang masih memerlukan logo

| Kod | Sekolah | PPD | Negeri |
| --- | --- | --- | --- |
| CBC4052 | SEKOLAH JENIS KEBANGSAAN (CINA) POAY CHAI | PPD KUANTAN | Pahang |
| YCB1301 | SEKOLAH KEBANGSAAN EMPEROH JAMBU | PPD PADAWAN | Sarawak |
| YCC6111 | SEKOLAH JENIS KEBANGSAAN (CINA) SING MING | PPD SARIKEI | Sarawak |

Untuk CBC4052, [direktori](https://www.apac.com.my/cbc4052-sjkc-poay-chai.html) menyenaraikan Kampung Tiram, PPD Kuantan, dan [senarai sekolah Cina Pahang](https://zh.wikipedia.org/wiki/彭亨州华文小学列表) memaparkan status lokasi dan bilangan murid sebagai tidak berkenaan. Kod ini memerlukan pengesahan PPD Kuantan. Dua sekolah Sarawak masih memerlukan imej lencana yang dapat dipadankan dengan kod sekolah.
